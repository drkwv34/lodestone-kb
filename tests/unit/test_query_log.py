# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from lodestone.config import Config, Log, Workspace
from lodestone.storage.db import open_database
from lodestone.workspace import search_result, stats_workspace


def test_fr_081_default_query_log_stores_no_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "index.db"
    open_database(db).close()
    config = Config(workspace=Workspace(db_path=db))
    search_result(config, "secret-query-text-should-not-persist", limit=1)
    connection = open_database(db)
    try:
        row = connection.execute(
            "SELECT qhash, query_text, results, lanes FROM query_log"
        ).fetchone()
        assert row is not None
        assert row[0]
        assert row[1] is None
        assert "secret-query-text-should-not-persist" not in (row[1] or "")
    finally:
        connection.close()
    stored = Config(workspace=Workspace(db_path=db), log=Log(store_queries=True))
    search_result(stored, "visible-query", limit=1)
    connection = open_database(db)
    try:
        texts = [item[0] for item in connection.execute("SELECT query_text FROM query_log")]
        assert None in texts
        assert "visible-query" in texts
    finally:
        connection.close()
    summary = stats_workspace(config)
    assert summary["query_log"] >= 2
    assert summary["store_queries"] is False
