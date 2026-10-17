# SPDX-License-Identifier: Apache-2.0
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lodestone.cli import app
from lodestone.storage import db
from lodestone.storage.db import (
    SCHEMA_VERSION,
    StorageError,
    inspect_database,
    migrate,
    open_database,
    schema_version,
)


def test_fr_082_migration_apply_schema_and_idempotence(tmp_path: Path) -> None:
    path = tmp_path / "index.db"
    connection = open_database(path)
    try:
        assert schema_version(connection) == SCHEMA_VERSION
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert {
            "meta",
            "sources",
            "projects",
            "project_sources",
            "records",
            "records_fts",
            "term_stats",
            "card_cache",
            "embeddings",
            "llm_log",
            "query_log",
        } <= tables
        assert not {"eval_runs", "eval_results"} & tables
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        connection.execute("INSERT INTO meta VALUES ('sentinel', 'keep')")
        connection.commit()
        migrate(connection)
        assert connection.execute("SELECT value FROM meta WHERE key='sentinel'").fetchone() == (
            "keep",
        )
        # External-content reads must succeed, including the corrected norm_text column.
        assert connection.execute("SELECT * FROM records_fts").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO project_sources VALUES (999, 999)")
        connection.rollback()
    finally:
        connection.close()
    assert inspect_database(path) == SCHEMA_VERSION


def test_fr_082_newer_version_refused_without_mutation(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION + 1}")
        connection.execute("CREATE TABLE future(value TEXT)")
        connection.execute("INSERT INTO future VALUES ('preserved')")
    before = path.read_bytes()
    with pytest.raises(StorageError, match=r"newer.*upgrade"):
        open_database(path)
    assert path.read_bytes() == before
    assert not Path(str(path) + "-wal").exists()
    with pytest.raises(StorageError, match="newer"):
        inspect_database(path)


def test_fr_082_failed_migration_rolls_back_ddl_and_version(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0001_broken.sql").write_text("CREATE TABLE transient(x); INVALID SQL;")
    connection = sqlite3.connect(tmp_path / "index.db")
    try:
        with pytest.raises(StorageError, match=r"Migration 0001_broken\.sql failed"):
            migrate(connection, migrations)
        assert schema_version(connection) == 0
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []
        assert not connection.in_transaction
    finally:
        connection.close()


def test_fr_082_missing_migration_and_active_transaction(tmp_path: Path) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        with pytest.raises(StorageError, match="exactly one"):
            migrate(connection, tmp_path)
        connection.execute("BEGIN")
        with pytest.raises(StorageError, match="active transaction"):
            migrate(connection)
    finally:
        connection.close()


def test_fr_082_forward_upgrade_from_v1_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = sqlite3.connect(tmp_path / "index.db")
    connection.executescript((db.MIGRATIONS / "0001_init.sql").read_text())
    connection.execute("PRAGMA user_version=1")
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0002_fixture.sql").write_text("ALTER TABLE meta ADD COLUMN note TEXT;")
    monkeypatch.setattr(db, "SCHEMA_VERSION", 2)
    try:
        migrate(connection, migrations)
        assert schema_version(connection) == 2
        columns = {row[1] for row in connection.execute("PRAGMA table_info(meta)")}
        assert "note" in columns
        migrate(connection, migrations)
    finally:
        connection.close()


def test_fr_001_init_runtime_error_on_newer_database(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    with sqlite3.connect(tmp_path / ".lodestone/index.db") as connection:
        connection.execute("PRAGMA user_version=99")
    result = CliRunner().invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 1
    assert "newer" in result.output


def test_fr_032_migration_0002_backfills_existing_v1(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "v1.db")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript((db.MIGRATIONS / "0001_init.sql").read_text())
        connection.execute("PRAGMA user_version=1")
        connection.execute("INSERT INTO sources VALUES(1,'wiki','files','{}',NULL)")
        connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,text,content_hash,"
            "created_at,updated_at,indexed_at) "
            "VALUES(1,'legacy','doc','ERR_LEGACY café café','h','','','')"
        )
        connection.commit()
        migrate(connection)
        assert schema_version(connection) == SCHEMA_VERSION
        assert connection.execute(
            "SELECT rowid FROM records_fts WHERE records_fts MATCH ?",
            ('"ERR_LEGACY"',),
        ).fetchone() == (1,)
        assert dict(connection.execute("SELECT term,df FROM term_stats")) == {
            "err_legacy": 1,
            "cafe": 1,
        }
        assert connection.execute("SELECT value FROM meta WHERE key='record_count'").fetchone() == (
            "1",
        )
        connection.execute("INSERT INTO records_fts(records_fts,rank) VALUES('integrity-check',1)")
    finally:
        connection.close()
