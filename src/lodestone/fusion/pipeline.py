# SPDX-License-Identifier: Apache-2.0
"""Run available lanes, fuse ranks, decay, collapse, expand and emit evidence."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, cast

from lodestone.config import Config, Lane
from lodestone.fusion.collapse import Ranked, collapse
from lodestone.fusion.decay import apply_decay
from lodestone.fusion.expand import neighbours
from lodestone.fusion.packet import (
    Evidence,
    EvidenceChild,
    EvidenceNeighbour,
    Explain,
    LaneExplain,
    packet_from_row,
    validate_packet,
)
from lodestone.fusion.rrf import rrf
from lodestone.lanes.fts import Hit, LaneName
from lodestone.lanes.fts import search as fts_search
from lodestone.lanes.grep import search as grep_search
from lodestone.lanes.result import SearchResult
from lodestone.lanes.scope import Scope
from lodestone.lanes.vec import VecLane
from lodestone.lanes.vec import search as vec_search
from lodestone.providers import Chat
from lodestone.rerank import apply as apply_rerank
from lodestone.vectors.embedder import Embedder

FTS_LANES: tuple[LaneName, ...] = ("fts_raw", "fts_card", "fts_rare")
VEC_LANES: tuple[LaneName, ...] = ("vec_card", "vec_chunk")
ROW_SQL = (
    "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.text,r.metadata_json,r.updated_at,"
    "r.parent_id,r.author,r.authors_json,r.card_json,r.seq FROM records r "
    "JOIN sources s ON s.id=r.source_id WHERE r.id=?"
)


def _row(connection: sqlite3.Connection, record_id: int) -> dict[str, Any] | None:
    fetched = connection.execute(ROW_SQL, (record_id,)).fetchone()
    if fetched is None:
        return None
    metadata = json.loads(fetched[6] or "{}")
    authors = json.loads(fetched[10] or "[]") if fetched[10] else []
    card = json.loads(fetched[11]) if fetched[11] else None
    snippet = str(fetched[5] or "").replace("\n", " ")[:240]
    return {
        "id": int(fetched[0]),
        "ext_id": str(fetched[1]),
        "source": str(fetched[2]),
        "kind": str(fetched[3]),
        "title": str(fetched[4] or ""),
        "text": str(fetched[5] or ""),
        "uri": str(metadata.get("uri", "")),
        "updated_at": str(fetched[7] or ""),
        "parent_id": None if fetched[8] is None else int(fetched[8]),
        "author": fetched[9],
        "authors": authors if isinstance(authors, list) else [],
        "card": card if isinstance(card, dict) else None,
        "seq": int(fetched[12] or 0),
        "snippet": snippet,
        "metadata": metadata,
    }


def _hit_from_evidence(packet: Evidence, ext_id: str) -> Hit:
    known: dict[str, LaneName] = {
        "fts_raw": "fts_raw",
        "fts_card": "fts_card",
        "fts_rare": "fts_rare",
        "vec_card": "vec_card",
        "vec_chunk": "vec_chunk",
        "grep": "grep",
    }
    best = "fts_raw"
    if packet.lanes:
        best = max(packet.lanes.items(), key=lambda item: item[1].contribution)[0]
    lane = known.get(best, "fts_raw")
    return Hit(
        id=packet.id,
        ext_id=ext_id,
        source=packet.source,
        kind=packet.kind,
        title=packet.title,
        uri=packet.uri,
        snippet=packet.snippet,
        score=packet.score,
        lane=lane,
        updated_at=packet.updated_at,
        parent_id=None,
    )


def _run_lane(
    connection: sqlite3.Connection,
    config: Config,
    query: str,
    lane: Lane,
    scope: Scope,
    *,
    limit: int,
    regex: bool,
    embedder: Embedder | None,
) -> SearchResult:
    if lane in FTS_LANES:
        hits = fts_search(
            connection,
            query,
            lane=lane,
            scope=scope,
            limit=limit,
            rare_idf=config.retrieval.rare_idf,
            rare_df_ratio=config.retrieval.rare_df_ratio,
        )
        return SearchResult(hits, [], lane)
    if lane in VEC_LANES:
        return vec_search(
            connection,
            query,
            lane=cast(VecLane, lane),
            embedder=embedder,
            scope=scope,
            limit=limit,
        )
    if lane == "grep":
        return grep_search(connection, query, regex=regex, scope=scope, limit=limit)
    return SearchResult([], [f"{lane} skipped: unknown lane"], str(lane))


def fused_search(
    connection: sqlite3.Connection,
    config: Config,
    query: str,
    *,
    scope: Scope,
    limit: int = 10,
    decay: bool = True,
    explain: bool = False,
    regex: bool = False,
    include_grep: bool = False,
    embedder: Embedder | None = None,
    now: datetime | None = None,
    rerank: bool | None = None,
    chat: Chat | None = None,
) -> SearchResult:
    retrieval = config.retrieval
    enabled = list(retrieval.lanes)
    if not include_grep:
        enabled = [lane for lane in enabled if lane != "grep"]
    per_lane = max(limit, retrieval.candidate_pool) * 3
    lists: dict[str, list[int]] = {}
    raw_scores: dict[str, dict[int, float]] = {}
    hits_by_id: dict[int, Hit] = {}
    notices: list[str] = []
    for lane in enabled:
        result = _run_lane(
            connection,
            config,
            query,
            lane,
            scope,
            limit=per_lane,
            regex=regex,
            embedder=embedder,
        )
        notices.extend(result.notices)
        if not result.hits:
            continue
        lists[lane] = [hit.id for hit in result.hits]
        raw_scores[lane] = {hit.id: hit.score for hit in result.hits}
        for hit in result.hits:
            hits_by_id.setdefault(hit.id, hit)
    weights = {str(name): float(weight) for name, weight in retrieval.weights.items()}
    fused = rrf(lists, weights, k=retrieval.rrf_k, raw_scores=raw_scores)
    clock = now or datetime.now(UTC)
    ranked: list[Ranked] = []
    decayed: dict[int, tuple[float, float]] = {}
    for record_id, score in fused.items():
        hit = hits_by_id[record_id]
        final, factor = apply_decay(
            score.rrf,
            hit.updated_at,
            kind=hit.kind,
            table=retrieval.decay,
            now=clock,
            enabled=decay,
        )
        decayed[record_id] = (final, factor)
        ranked.append(
            Ranked(
                id=record_id,
                parent_id=hit.parent_id,
                source=hit.source,
                score=final,
                updated_at=hit.updated_at,
            )
        )
    ranked.sort(key=lambda item: (item.score, item.updated_at, -item.id), reverse=True)
    selected = collapse(
        ranked, max_per_source=retrieval.max_per_source, pool=retrieval.candidate_pool
    )
    rerank_scores: dict[int, float] = {}
    want_rerank = retrieval.rerank if rerank is None else rerank
    keep = limit
    if want_rerank:
        pool: list[tuple[int, str, float]] = []
        by_id = {item.id: item for item in selected}
        for item in selected:
            row = _row(connection, item.id)
            text = "" if row is None else str(row.get("text") or row.get("snippet") or "")
            pool.append((item.id, text, item.score))
        outcome = apply_rerank(query, pool, chat, keep=retrieval.rerank_keep)
        selected = [by_id[ident] for ident in outcome.order if ident in by_id]
        rerank_scores = outcome.scores
        if outcome.notice:
            notices.append(outcome.notice)
        elif outcome.scores:
            keep = min(limit, retrieval.rerank_keep)
    packets: list[dict[str, object]] = []
    hits: list[Hit] = []
    for item in selected[:keep]:
        member = max(item.member_ids, key=lambda ident: decayed.get(ident, (0.0, 1.0))[0])
        fused_score = fused[member]
        final, factor = decayed[member]
        row = _row(connection, item.id) or _row(connection, member)
        if row is None:
            continue
        if member in hits_by_id and hits_by_id[member].snippet:
            row["snippet"] = hits_by_id[member].snippet
        lanes = {
            name: LaneExplain(
                rank=contrib.rank,
                raw_score=contrib.raw_score,
                contribution=contrib.contribution,
                score=contrib.raw_score,
            )
            for name, contrib in fused_score.lanes.items()
        }
        children = [
            EvidenceChild(
                id=child_id,
                kind=str(child_row["kind"]),
                snippet=str(child_row["snippet"]),
                title=str(child_row["title"]),
            )
            for child_id in item.matched_children
            if (child_row := _row(connection, child_id)) is not None
        ]
        neighbour_models = [
            EvidenceNeighbour.model_validate(entry)
            for entry in neighbours(
                connection, member, n=retrieval.expand, max_chars=retrieval.expand_max_chars
            )
        ]
        explain_obj = (
            Explain(
                lanes=lanes,
                rrf=fused_score.rrf,
                decay_factor=factor,
                rerank_score=rerank_scores.get(item.id),
                final=final,
            )
            if explain
            else None
        )
        packet = packet_from_row(
            row,
            score=final,
            lanes=lanes,
            children=children,
            neighbours=neighbour_models,
            explain=explain_obj,
        )
        payload = packet.model_dump(by_alias=True)
        if explain_obj is None:
            payload.pop("explain", None)
        else:
            payload["explain"] = {
                **{name: model.model_dump() for name, model in explain_obj.lanes.items()},
                "rrf": explain_obj.rrf,
                "decay_factor": explain_obj.decay_factor,
                "rerank_score": explain_obj.rerank_score,
                "final": explain_obj.final,
            }
        check = {key: value for key, value in payload.items() if key != "explain"}
        validate_packet(check)
        packets.append(payload)
        hits.append(_hit_from_evidence(packet, str(row["ext_id"])))
    return SearchResult(hits, notices, "fused", packets)
