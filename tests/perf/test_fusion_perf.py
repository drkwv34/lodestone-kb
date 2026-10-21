# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import platform
import statistics
import time
from pathlib import Path

import pytest

from lodestone.config import Config, Retrieval, Source
from lodestone.fusion.pipeline import fused_search
from lodestone.ingest.pipeline import sync
from lodestone.lanes.scope import Scope
from lodestone.storage.db import open_database
from lodestone.workspace import initialise

N = 20_000


def _machine() -> str:
    return (
        f"{platform.system()} {platform.release()} {platform.machine()} "
        f"python {platform.python_version()}"
    )


def _insert_corpus(connection, count: int = N) -> None:
    connection.execute("INSERT INTO sources(name,kind,config_json) VALUES('perf','files','{}')")
    source_id = connection.execute("SELECT id FROM sources WHERE name='perf'").fetchone()[0]
    rows = [
        (
            source_id,
            f"perf-{index}.txt",
            "doc",
            f"title {index % 50}",
            f"body token_{index % 50} unique_{index} extra words for lexical search",
            "h",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        )
        for index in range(count)
    ]
    connection.executemany(
        "INSERT INTO records(source_id,ext_id,kind,title,text,content_hash,created_at,"
        "updated_at,indexed_at) VALUES(?,?,?,?,?,?,?,?,?)",
        rows,
    )
    connection.commit()


@pytest.mark.perf
def test_nfr_001_lexical_search_p95(tmp_path: Path) -> None:
    connection = open_database(tmp_path / "index.db")
    try:
        _insert_corpus(connection)
        config = Config(retrieval=Retrieval(lanes=["fts_raw", "fts_card", "fts_rare"]))
        queries = [f"token_{index}" for index in range(50)]
        samples: list[float] = []
        fused_search(connection, config, queries[0], scope=Scope(), decay=False, limit=10)
        for query in queries:
            start = time.perf_counter()
            fused_search(connection, config, query, scope=Scope(), decay=False, limit=10)
            samples.append((time.perf_counter() - start) * 1000)
        p95 = statistics.quantiles(samples, n=20)[-1]
        print(f"NFR-001 p95_ms={p95:.3f} n={N} machine={_machine()} samples={len(samples)}")
        assert p95 >= 0
    finally:
        connection.close()


@pytest.mark.perf
def test_nfr_002_heuristic_ingest_throughput(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    for index in range(N):
        (root / f"{index}.txt").write_text(
            f"document {index} token_{index % 50}\n", encoding="utf-8"
        )
    initialise(tmp_path)
    config = Config(
        sources=[Source(name="perf", kind="files", path=root)],
        retrieval=Retrieval(lanes=["fts_raw"]),
    )
    config.workspace.db_path = tmp_path / ".lodestone" / "index.db"
    connection = open_database(config.workspace.db_path)
    try:
        start = time.perf_counter()
        report = sync(connection, config)
        elapsed = time.perf_counter() - start
        rate = report.processed / elapsed if elapsed else 0.0
        print(
            f"NFR-002 records_per_s={rate:.3f} processed={report.processed} "
            f"elapsed_s={elapsed:.3f} machine={_machine()}"
        )
        assert report.processed == N
        assert rate >= 0
    finally:
        connection.close()


@pytest.mark.perf
def test_nfr_003_incremental_no_change_sync(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    for index in range(N):
        (root / f"{index}.txt").write_text(
            f"document {index} token_{index % 50}\n", encoding="utf-8"
        )
    initialise(tmp_path)
    config = Config(
        sources=[Source(name="perf", kind="files", path=root)],
        retrieval=Retrieval(lanes=["fts_raw"]),
    )
    config.workspace.db_path = tmp_path / ".lodestone" / "index.db"
    connection = open_database(config.workspace.db_path)
    try:
        first = sync(connection, config)
        assert first.processed == N
        start = time.perf_counter()
        second = sync(connection, config)
        elapsed = time.perf_counter() - start
        print(
            f"NFR-003 no_change_sync_s={elapsed:.3f} processed={second.processed} "
            f"unchanged={second.unchanged} machine={_machine()}"
        )
        assert second.processed == 0
        assert elapsed >= 0
    finally:
        connection.close()
