# SPDX-License-Identifier: Apache-2.0
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lodestone.cli import app
from lodestone.storage.db import StorageError, probe_fts5


def test_fr_080_fts5_identifier_probe() -> None:
    probe_fts5()


def test_fr_080_disabled_fts5_reports_remediation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    real_connect = sqlite3.connect

    def no_fts5(database: str, **kwargs: object) -> sqlite3.Connection:
        if database == ":memory:":
            raise sqlite3.OperationalError("no such module: fts5")
        return real_connect(database, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", no_fts5)
    with pytest.raises(StorageError, match=r"FTS5 unavailable.*python\.org"):
        probe_fts5()
    result = runner.invoke(app, ["doctor", "--config", str(tmp_path / "lodestone.toml")])
    assert result.exit_code == 1
    assert "FTS5 unavailable" in result.output
    assert "python.org" in result.output


def test_fr_080_missing_and_outdated_database(tmp_path: Path) -> None:
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text("schema_version = 1")
    result = CliRunner().invoke(app, ["doctor", "--config", str(config_path)])
    assert result.exit_code == 1
    assert "run lodestone init" in result.output
    assert not (tmp_path / ".lodestone/index.db").exists()
    (tmp_path / ".lodestone").mkdir()
    connection = sqlite3.connect(tmp_path / ".lodestone/index.db")
    connection.close()
    result = CliRunner().invoke(app, ["doctor", "--config", str(config_path)])
    assert result.exit_code == 1
    assert "requires migration" in result.output


def test_fr_080_doctor_complete(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    result = runner.invoke(app, ["doctor", "--config", str(tmp_path / "lodestone.toml")])
    assert result.exit_code == 0, result.output
    assert "sqlite-vec:" in result.output
    assert "Provider: skipped" in result.output
    assert "Doctor: OK" in result.output
    deep = runner.invoke(
        app, ["doctor", "--deep", "--offline", "--config", str(tmp_path / "lodestone.toml")]
    )
    assert deep.exit_code == 0, deep.output
    assert "Deep:" in deep.output


def test_nfr_006_doctor_deep_missing_fts(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    from lodestone.config import load_config
    from lodestone.storage.db import open_database

    config = load_config(tmp_path / "lodestone.toml")
    connection = open_database(config.workspace.db_path)
    try:
        connection.execute(
            "INSERT OR IGNORE INTO sources(name,kind,config_json) VALUES('x','files','{}')"
        )
        source_id = connection.execute("SELECT id FROM sources WHERE name='x'").fetchone()[0]
        cursor = connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,title,text,content_hash,"
            "created_at,updated_at,indexed_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                source_id,
                "gone.md",
                "doc",
                "t",
                "body",
                "h",
                "2026-01-01",
                "2026-01-01",
                "2026-01-01",
            ),
        )
        record_id = int(cursor.lastrowid or 0)
        connection.execute(
            "INSERT INTO records_fts(records_fts, rowid, title, text) "
            "VALUES('delete', ?, 't', 'body')",
            (record_id,),
        )
        connection.commit()
    finally:
        connection.close()
    result = runner.invoke(app, ["doctor", "--deep", "--config", str(tmp_path / "lodestone.toml")])
    assert result.exit_code == 1
    assert "FTS" in result.output
