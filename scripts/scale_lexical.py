# SPDX-License-Identifier: Apache-2.0
"""Measure a 200,000-record lexical-only index (NFR-004)."""

from __future__ import annotations

import os
import resource
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from lodestone.ingest.reindex import rebuild_fts
from lodestone.lanes.fts import search
from lodestone.storage.db import open_database
from lodestone.workspace import initialise


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    value = float(usage.ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024 * 1024)
    return value / 1024


def bulk_insert(connection: sqlite3.Connection, count: int) -> None:
    """Load rows without per-row FTS triggers, then rebuild indexes once."""
    connection.execute(
        "INSERT OR IGNORE INTO sources(name,kind,config_json) VALUES('scale','files','{}')"
    )
    source_id = int(connection.execute("SELECT id FROM sources WHERE name='scale'").fetchone()[0])
    now = "2026-10-26T00:00:00+00:00"
    with connection:
        connection.execute("DROP TRIGGER IF EXISTS records_ai")
        connection.execute("DROP TRIGGER IF EXISTS records_au")
        connection.execute("DROP TRIGGER IF EXISTS records_ad")
        batch = 5000
        for start in range(0, count, batch):
            rows = [
                (
                    source_id,
                    f"doc-{index}.txt",
                    "doc",
                    f"Title {index}",
                    f"Record {index} SCALE_TOKEN_{index % 17} lexical payload.",
                    f"h{index}",
                    now,
                    now,
                    now,
                )
                for index in range(start, min(start + batch, count))
            ]
            connection.executemany(
                "INSERT INTO records(source_id,ext_id,kind,title,text,content_hash,"
                "created_at,updated_at,indexed_at) VALUES(?,?,?,?,?,?,?,?,?)",
                rows,
            )


def main() -> None:
    count = int(os.environ.get("LODESTONE_SCALE_N", "200000"))
    default_dir = Path(tempfile.gettempdir()) / "lodestone-scale"
    root = Path(os.environ.get("LODESTONE_SCALE_DIR", str(default_dir)))
    if root.exists():
        raise SystemExit(f"refusing to overwrite {root}")
    initialise(root)
    db_path = root / ".lodestone/index.db"
    connection = open_database(db_path)
    started = time.monotonic()
    bulk_insert(connection, count)
    with connection:
        rebuild_fts(connection)
    insert_s = time.monotonic() - started
    size = db_path.stat().st_size
    query = "SCALE_TOKEN_3"
    search_started = time.monotonic()
    hits = search(connection, query, lane="fts_raw", limit=10)
    search_ms = (time.monotonic() - search_started) * 1000
    memory = rss_mb()
    n = int(connection.execute("SELECT count(*) FROM records WHERE tombstoned=0").fetchone()[0])
    connection.close()
    print(f"records={n}")
    print(f"insert_s={insert_s:.2f}")
    print(f"db_bytes={size}")
    print(f"db_gb={size / (1024**3):.4f}")
    print(f"search_ms={search_ms:.2f}")
    print(f"search_hits={len(hits)}")
    print(f"rss_mb={memory:.1f}")


if __name__ == "__main__":
    main()
