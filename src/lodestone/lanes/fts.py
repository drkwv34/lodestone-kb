# SPDX-License-Identifier: Apache-2.0
"""Safe FTS5 expressions and single-lane BM25 retrieval."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Literal

from lodestone.lanes.scope import Scope
from lodestone.lanes.scope import clauses as filter_clauses
from lodestone.storage.terms import rare_terms
from lodestone.tokenize import tokenize

LaneName = Literal["fts_raw", "fts_card", "fts_rare", "vec_card", "vec_chunk", "grep"]
MAX_CLAUSES = 64
LANE_COLUMNS: dict[LaneName, str] = {
    "fts_raw": "title text",
    "fts_card": "norm_text",
    "fts_rare": "title text",
}
LANE_SQL: dict[LaneName, tuple[str, str]] = {
    "fts_raw": (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,"
        "snippet(records_fts,1,'[',']',' … ',32),bm25(records_fts,3.0,1.0),r.updated_at,"
        "r.parent_id "
        "FROM records_fts JOIN records r ON r.id=records_fts.rowid "
        "JOIN sources s ON s.id=r.source_id WHERE ",
        " ORDER BY bm25(records_fts,3.0,1.0),r.updated_at DESC,r.id LIMIT ?",
    ),
    "fts_card": (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,"
        "snippet(records_card_fts,0,'[',']',' … ',32),bm25(records_card_fts),r.updated_at,"
        "r.parent_id "
        "FROM records_card_fts JOIN records r ON r.id=records_card_fts.rowid "
        "JOIN sources s ON s.id=r.source_id WHERE ",
        " ORDER BY bm25(records_card_fts),r.updated_at DESC,r.id LIMIT ?",
    ),
    "fts_rare": (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,"
        "snippet(records_fts,1,'[',']',' … ',32),bm25(records_fts,3.0,1.0),r.updated_at,"
        "r.parent_id "
        "FROM records_fts JOIN records r ON r.id=records_fts.rowid "
        "JOIN sources s ON s.id=r.source_id WHERE ",
        " ORDER BY bm25(records_fts,3.0,1.0),r.updated_at DESC,r.id LIMIT ?",
    ),
}


def quote(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def sanitise(query: str, columns: str = "title text") -> str:
    """Preserve phrases/trailing prefix stars, OR-expand words, quote all user syntax.

    Limit clauses to avoid FTS parser depth limits even for adversarial inputs.
    Unmatched quotes and punctuation degrade to literal token searches.
    """
    clauses: list[str] = []
    for match in re.finditer(r'"([^"]*)"(\*)?|([^\s"]+)', query[:16384]):
        phrase, prefix, word = match.groups()
        tokens = tokenize(phrase if phrase is not None else word)
        if phrase is not None and tokens:
            clauses.append(quote(" ".join(tokens)) + ("*" if prefix else ""))
        else:
            for index, token in enumerate(tokens):
                suffix = "*" if word.endswith("*") and index == len(tokens) - 1 else ""
                clauses.append(quote(token) + suffix)
        if len(clauses) >= MAX_CLAUSES:
            break
    unique = list(dict.fromkeys(clauses))[:MAX_CLAUSES]
    return "{" + columns + "} : (" + " OR ".join(unique) + ")" if unique else ""


@dataclass(frozen=True)
class Hit:
    id: int
    ext_id: str
    source: str
    kind: str
    title: str
    uri: str
    snippet: str
    score: float
    lane: LaneName
    updated_at: str
    parent_id: int | None = None


def search(
    connection: sqlite3.Connection,
    query: str,
    *,
    lane: LaneName = "fts_raw",
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    authors: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
    metadata: dict[str, str] | None = None,
    scope: Scope | None = None,
    limit: int = 10,
    rare_idf: float = 4.0,
    rare_df_ratio: float | None = None,
) -> list[Hit]:
    if lane not in LANE_COLUMNS:
        raise ValueError("lane must be fts_raw, fts_card or fts_rare")
    if limit < 1:
        raise ValueError("limit must be positive")
    columns = LANE_COLUMNS[lane]
    prefix, suffix = LANE_SQL[lane]
    if lane == "fts_rare":
        terms = rare_terms(connection, tokenize(query[:16384]), rare_idf, rare_df_ratio)
        expression = sanitise(" ".join(quote(term) for term in terms[:MAX_CLAUSES]), columns)
    else:
        expression = sanitise(query, columns)
    if not expression:
        return []
    filters = scope or Scope(
        sources=sources, kinds=kinds, authors=authors, since=since, until=until, metadata=metadata
    )
    extra, extra_params = filter_clauses(filters)
    match = "records_card_fts MATCH ?" if lane == "fts_card" else "records_fts MATCH ?"
    where = [match, *extra]
    parameters: list[object] = [expression, *extra_params, limit]
    sql = prefix + " AND ".join(where) + suffix
    return [
        Hit(
            id=row[0],
            ext_id=row[1],
            source=row[2],
            kind=row[3],
            title=row[4],
            uri=str(json.loads(row[5]).get("uri", "")),
            snippet=row[6],
            score=-float(row[7]),
            lane=lane,
            updated_at=row[8],
            parent_id=None if row[9] is None else int(row[9]),
        )
        for row in connection.execute(sql, parameters)
    ]
