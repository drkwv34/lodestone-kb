# SPDX-License-Identifier: Apache-2.0
"""Optional vec_card and vec_chunk lanes over stored embeddings."""

from __future__ import annotations

import json
import sqlite3
from typing import Literal

from lodestone.lanes.fts import Hit
from lodestone.lanes.result import SearchResult
from lodestone.storage.embeddings import matching_count
from lodestone.vectors.backends import BruteForceBackend, SqliteVecBackend, sqlite_vec_available
from lodestone.vectors.embedder import Embedder

VecLane = Literal["vec_card", "vec_chunk"]
VEC_KINDS: dict[VecLane, tuple[str, ...]] = {
    "vec_card": ("card",),
    "vec_chunk": ("chunk", "burst"),
}


def search(
    connection: sqlite3.Connection,
    query: str,
    *,
    lane: VecLane,
    embedder: Embedder | None,
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    limit: int = 10,
) -> SearchResult:
    if limit < 1:
        raise ValueError("limit must be positive")
    if embedder is None:
        return SearchResult([], [f"{lane} skipped: embeddings disabled"], lane)
    embed_kinds = VEC_KINDS[lane]
    matched = matching_count(connection, embedder.model, embedder.dim, embed_kinds)
    if matched == 0:
        total = connection.execute("SELECT count(*) FROM embeddings").fetchone()
        if total and int(total[0]) > 0:
            notice = f"{lane} skipped: embeddings model/dim mismatch; reindex --lanes vec"
        else:
            notice = f"{lane} skipped: embeddings unavailable"
        return SearchResult([], [notice], lane)
    rows = _load_rows(
        connection,
        embedder.model,
        embedder.dim,
        embed_kinds,
        sources=sources,
        kinds=kinds,
    )
    if not rows:
        return SearchResult([], [], lane)
    vector = embedder.embed([query])[0]
    if sqlite_vec_available():
        matches = SqliteVecBackend().query(
            rows, vector, limit, model=embedder.model, dim=embedder.dim
        )
    else:
        matches = BruteForceBackend().query(rows, vector, limit)
    hits = [_hit(connection, match.record_id, match.score, lane) for match in matches]
    return SearchResult([hit for hit in hits if hit is not None], [], lane)


def _load_rows(
    connection: sqlite3.Connection,
    model: str,
    dim: int,
    embed_kinds: tuple[str, ...],
    *,
    sources: list[str] | None,
    kinds: list[str] | None,
) -> list[tuple[int, bytes]]:
    placeholders = ",".join("?" for _ in embed_kinds)
    where = [
        "r.tombstoned=0",
        "e.model=?",
        "e.dim=?",
        f"e.kind IN ({placeholders})",
    ]
    parameters: list[object] = [model, dim, *embed_kinds]
    if sources is not None:
        if not sources:
            return []
        where.append("s.name IN (" + ",".join("?" for _ in sources) + ")")
        parameters.extend(sources)
    if kinds is not None:
        if not kinds:
            return []
        where.append("r.kind IN (" + ",".join("?" for _ in kinds) + ")")
        parameters.extend(kinds)
    prefix = (
        "SELECT e.record_id, e.vec FROM embeddings e "
        "JOIN records r ON r.id=e.record_id JOIN sources s ON s.id=r.source_id WHERE "
    )
    sql = prefix + " AND ".join(where)
    return [
        (int(record_id), bytes(blob)) for record_id, blob in connection.execute(sql, parameters)
    ]


def _hit(connection: sqlite3.Connection, record_id: int, score: float, lane: VecLane) -> Hit | None:
    row = connection.execute(
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,r.text,r.updated_at "
        "FROM records r JOIN sources s ON s.id=r.source_id WHERE r.id=?",
        (record_id,),
    ).fetchone()
    if row is None:
        return None
    snippet = str(row[6]).replace("\n", " ")[:240]
    return Hit(
        id=row[0],
        ext_id=row[1],
        source=row[2],
        kind=row[3],
        title=row[4],
        uri=str(json.loads(row[5]).get("uri", "")),
        snippet=snippet,
        score=float(score),
        lane=lane,
        updated_at=row[7],
    )
