# SPDX-License-Identifier: Apache-2.0
"""Safe FTS5 expressions and single-lane BM25 retrieval."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Literal

from lodestone.storage.terms import rare_terms
from lodestone.tokenize import tokenize

LaneName = Literal["fts_raw", "fts_rare"]
MAX_CLAUSES = 64


def quote(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def sanitise(query: str) -> str:
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
    return "{title text} : (" + " OR ".join(unique) + ")" if unique else ""


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


def search(
    connection: sqlite3.Connection,
    query: str,
    *,
    lane: LaneName = "fts_raw",
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    limit: int = 10,
    rare_idf: float = 4.0,
    rare_df_ratio: float | None = None,
) -> list[Hit]:
    if lane not in ("fts_raw", "fts_rare"):
        raise ValueError("lane must be fts_raw or fts_rare")
    if limit < 1:
        raise ValueError("limit must be positive")
    if lane == "fts_rare":
        terms = rare_terms(connection, tokenize(query[:16384]), rare_idf, rare_df_ratio)
        expression = sanitise(" ".join(quote(term) for term in terms[:MAX_CLAUSES]))
    else:
        expression = sanitise(query)
    if not expression:
        return []
    where = ["records_fts MATCH ?", "r.tombstoned=0"]
    parameters: list[str | int] = [expression]
    for column, values in (("s.name", sources), ("r.kind", kinds)):
        if values is not None:
            if not values:
                return []
            where.append(column + " IN (" + ",".join("?" for _ in values) + ")")
            parameters.extend(values)
    parameters.append(limit)
    sql = (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,"
        "snippet(records_fts,1,'[',']',' … ',32),bm25(records_fts,3.0,1.0,0.0),r.updated_at "
        "FROM records_fts JOIN records r ON r.id=records_fts.rowid "
        "JOIN sources s ON s.id=r.source_id WHERE "
        + " AND ".join(where)
        + " ORDER BY bm25(records_fts,3.0,1.0,0.0),r.updated_at DESC,r.id LIMIT ?"
    )
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
        )
        for row in connection.execute(sql, parameters)
    ]
