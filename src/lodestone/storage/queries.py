# SPDX-License-Identifier: Apache-2.0
"""Query log writes; text is stored only when the caller supplies it."""

from __future__ import annotations

import hashlib
import sqlite3
from contextvars import ContextVar
from datetime import UTC, datetime

query_log_enabled: ContextVar[bool] = ContextVar("lodestone_query_log", default=True)


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def log_query(
    connection: sqlite3.Connection,
    *,
    query: str,
    project: str,
    lanes: str,
    results: int,
    latency_ms: int,
    store_text: bool,
) -> None:
    connection.execute(
        "INSERT INTO query_log(qhash, project, lanes, results, latency_ms, query_text, created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (
            query_hash(query),
            project,
            lanes,
            results,
            latency_ms,
            query if store_text else None,
            datetime.now(UTC).isoformat(),
        ),
    )


def count_queries(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT count(*) FROM query_log").fetchone()
    return int(row[0]) if row else 0
