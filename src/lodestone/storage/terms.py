# SPDX-License-Identifier: Apache-2.0
"""Raw/title document frequencies and BM25 inverse document frequency."""

import math
import sqlite3


def document_count(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT value FROM meta WHERE key='record_count'").fetchone()
    return int(row[0]) if row else 0


def idf(connection: sqlite3.Connection, term: str) -> float:
    """Compute ln(1 + (N - df + .5) / (df + .5)) over active records."""
    row = connection.execute("SELECT df FROM term_stats WHERE term=?", (term,)).fetchone()
    df = int(row[0]) if row else 0
    return math.log1p((document_count(connection) - df + 0.5) / (df + 0.5))


def rare_terms(
    connection: sqlite3.Connection,
    tokens: list[str],
    threshold: float = 4.0,
    df_ratio: float | None = None,
) -> list[str]:
    """Select known terms by IDF, or a configured corpus-relative df threshold."""
    count = document_count(connection)
    result: list[str] = []
    for term in dict.fromkeys(tokens):
        row = connection.execute("SELECT df FROM term_stats WHERE term=?", (term,)).fetchone()
        if row and (
            (df_ratio is not None and int(row[0]) / max(count, 1) <= df_ratio)
            or (df_ratio is None and idf(connection, term) >= threshold)
        ):
            result.append(term)
    return result
