# SPDX-License-Identifier: Apache-2.0
"""Author ranking and recency listing over in-scope records."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from lodestone.config import Config
from lodestone.fusion.decay import apply_decay
from lodestone.fusion.packet import Evidence, LaneExplain, packet_from_row
from lodestone.fusion.pipeline import ROW_SQL, fused_search
from lodestone.lanes.fts import Hit
from lodestone.lanes.scope import Scope, clauses

ROW_AUTHOR_SQL = (
    "SELECT r.id,r.author,r.authors_json,r.kind,r.updated_at,r.metadata_json "
    "FROM records r WHERE r.id=? AND r.tombstoned=0"
)


@dataclass(frozen=True)
class Expert:
    author: str
    score: float
    records: list[int]


def _authors(author: object, blob: object) -> list[str]:
    names: list[str] = []
    if isinstance(author, str) and author.strip():
        names.append(author.strip())
    if blob:
        parsed = json.loads(str(blob))
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str) and item.strip() and item.strip() not in names:
                    names.append(item.strip())
    return names


def _reactions(blob: object) -> int:
    if not blob:
        return 0
    parsed = json.loads(str(blob))
    if not isinstance(parsed, dict):
        return 0
    value = parsed.get("reactions", 0)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def who_knows(
    connection: sqlite3.Connection,
    config: Config,
    topic: str,
    *,
    scope: Scope,
    limit: int = 5,
    now: datetime | None = None,
) -> list[Expert]:
    result = fused_search(
        connection,
        config,
        topic,
        scope=scope,
        limit=max(50, config.retrieval.candidate_pool),
        decay=True,
        explain=False,
        rerank=False,
    )
    clock = now or datetime.now(UTC)
    totals: dict[str, float] = {}
    examples: dict[str, list[int]] = {}
    seen: set[tuple[str, int]] = set()
    for hit in result.hits:
        row = connection.execute(ROW_AUTHOR_SQL, (hit.id,)).fetchone()
        if row is None:
            continue
        ident, author, authors_json, kind, updated_at, metadata_json = row
        recency, _factor = apply_decay(
            1.0, str(updated_at or ""), kind=str(kind), table=config.retrieval.decay, now=clock
        )
        bonus = (1.0 if str(kind) == "burst" else 0.0) + (1.0 if _reactions(metadata_json) else 0.0)
        weight = recency * (1.0 + bonus)
        for name in _authors(author, authors_json):
            key = (name, int(ident))
            if key in seen:
                continue
            seen.add(key)
            totals[name] = totals.get(name, 0.0) + weight
            examples.setdefault(name, [])
            if int(ident) not in examples[name]:
                examples[name].append(int(ident))
    ranked = sorted(totals, key=lambda name: (totals[name], name), reverse=True)
    return [
        Expert(author=name, score=totals[name], records=examples[name][:8])
        for name in ranked[:limit]
    ]


def recent(
    connection: sqlite3.Connection,
    scope: Scope,
    *,
    limit: int = 10,
) -> list[Hit]:
    if limit < 1:
        raise ValueError("limit must be positive")
    where, parameters = clauses(scope)
    prefix = (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,r.text,r.updated_at,"
        "r.parent_id FROM records r JOIN sources s ON s.id=r.source_id WHERE "
    )
    sql = prefix + " AND ".join(where) + " ORDER BY r.updated_at DESC, r.id DESC LIMIT ?"
    hits: list[Hit] = []
    for row in connection.execute(sql, [*parameters, limit]):
        metadata = json.loads(row[5] or "{}")
        snippet = str(row[6] or "").replace("\n", " ")[:240]
        hits.append(
            Hit(
                id=int(row[0]),
                ext_id=str(row[1]),
                source=str(row[2]),
                kind=str(row[3]),
                title=str(row[4] or ""),
                uri=str(metadata.get("uri", "")),
                snippet=snippet,
                score=0.0,
                lane="fts_raw",
                updated_at=str(row[7] or ""),
                parent_id=None if row[8] is None else int(row[8]),
            )
        )
    return hits


def packets_for(connection: sqlite3.Connection, hits: list[Hit]) -> list[dict[str, object]]:
    packets: list[dict[str, object]] = []
    for hit in hits:
        fetched = connection.execute(ROW_SQL, (hit.id,)).fetchone()
        if fetched is None:
            continue
        metadata = json.loads(fetched[6] or "{}")
        authors = json.loads(fetched[10] or "[]") if fetched[10] else []
        card = json.loads(fetched[11]) if fetched[11] else None
        row = {
            "id": int(fetched[0]),
            "ext_id": str(fetched[1]),
            "source": str(fetched[2]),
            "kind": str(fetched[3]),
            "title": str(fetched[4] or ""),
            "text": str(fetched[5] or ""),
            "uri": str(metadata.get("uri", "")),
            "updated_at": str(fetched[7] or ""),
            "author": fetched[9],
            "authors": authors if isinstance(authors, list) else [],
            "card": card if isinstance(card, dict) else None,
            "snippet": hit.snippet,
        }
        packet: Evidence = packet_from_row(
            row, score=hit.score, lanes={"recent": LaneExplain(rank=1)}
        )
        payload = packet.model_dump(by_alias=True)
        payload.pop("explain", None)
        packets.append(payload)
    return packets
