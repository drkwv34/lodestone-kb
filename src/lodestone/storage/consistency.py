# SPDX-License-Identifier: Apache-2.0
"""Deep consistency checks used by doctor --deep (NFR-006)."""

from __future__ import annotations

import sqlite3

SAMPLE = 32


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master").fetchall()
    return {str(row[0]) for row in rows}


def _count(connection: sqlite3.Connection, sql: str) -> int:
    row = connection.execute(sql).fetchone()
    return int(row[0]) if row else 0


def deep_errors(connection: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    names = _table_names(connection)
    if "records_fts_docsize" in names:
        missing = _count(
            connection,
            "SELECT count(*) FROM records r WHERE r.tombstoned=0 AND NOT EXISTS "
            "(SELECT 1 FROM records_fts_docsize d WHERE d.id=r.id)",
        )
    else:
        missing = _count(
            connection,
            "SELECT count(*) FROM records r WHERE r.tombstoned=0 AND NOT EXISTS "
            "(SELECT 1 FROM records_fts f WHERE f.rowid=r.id)",
        )
    if missing:
        errors.append(f"{missing} non-tombstoned record(s) missing FTS rows")
    if "records_card_fts_docsize" in names:
        missing_card = _count(
            connection,
            "SELECT count(*) FROM records r WHERE r.tombstoned=0 AND r.norm_text!='' "
            "AND NOT EXISTS (SELECT 1 FROM records_card_fts_docsize d WHERE d.id=r.id)",
        )
    else:
        missing_card = _count(
            connection,
            "SELECT count(*) FROM records r WHERE r.tombstoned=0 AND r.norm_text!='' "
            "AND NOT EXISTS (SELECT 1 FROM records_card_fts f WHERE f.rowid=r.id)",
        )
    if missing_card:
        errors.append(f"{missing_card} card FTS row(s) missing")
    mismatches = 0
    for term, df in connection.execute(
        "SELECT term, df FROM term_stats ORDER BY df DESC, term LIMIT ?", (SAMPLE,)
    ):
        counted = connection.execute(
            "SELECT count(*) FROM record_terms WHERE term=?", (term,)
        ).fetchone()
        if counted and int(counted[0]) != int(df):
            mismatches += 1
    if mismatches:
        errors.append(f"term_stats df mismatch on {mismatches} sampled term(s)")
    for model, dims in connection.execute(
        "SELECT model, count(DISTINCT dim) FROM embeddings GROUP BY model"
    ):
        if int(dims) > 1:
            errors.append(f"embeddings for model {model} have mixed dimensions")
    orphans = connection.execute(
        "SELECT count(*) FROM records c LEFT JOIN records p ON p.id=c.parent_id "
        "WHERE c.parent_id IS NOT NULL AND p.id IS NULL"
    ).fetchone()
    if orphans and int(orphans[0]):
        errors.append(f"{orphans[0]} orphan child record(s)")
    return errors
