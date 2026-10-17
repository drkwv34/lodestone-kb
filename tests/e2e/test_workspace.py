# SPDX-License-Identifier: Apache-2.0
import json
import sqlite3
import subprocess
from pathlib import Path

from lodestone.storage.db import SCHEMA_VERSION


def command(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["lodestone", *args],  # noqa: S607
        cwd=directory,
        text=True,
        capture_output=True,
        check=False,
    )


def test_fr_001_init_idempotence_smoke(tmp_path: Path) -> None:
    first = command(tmp_path, "init")
    assert first.returncode == 0, first.stderr
    config = tmp_path / "lodestone.toml"
    with config.open("a") as stream:
        stream.write("\n# user comment preserved\n")
    before = config.read_bytes()
    with sqlite3.connect(tmp_path / ".lodestone/index.db") as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        connection.execute("INSERT INTO meta VALUES ('marker', 'preserved')")
    second = command(tmp_path, "init")
    assert second.returncode == 0, second.stderr
    assert "already initialised" in second.stdout
    assert config.read_bytes() == before
    with sqlite3.connect(tmp_path / ".lodestone/index.db") as connection:
        assert connection.execute("SELECT value FROM meta WHERE key='marker'").fetchone() == (
            "preserved",
        )


def test_fr_080_doctor_smoke(tmp_path: Path) -> None:
    assert command(tmp_path, "init").returncode == 0
    result = command(tmp_path, "doctor")
    assert result.returncode == 0, result.stderr
    for expected in (
        "Python:",
        "SQLite:",
        "FTS5: available",
        f"Database schema: {SCHEMA_VERSION}",
        "Doctor: OK",
    ):
        assert expected in result.stdout


def test_fr_002_config_show_smoke(tmp_path: Path) -> None:
    target = tmp_path / "child"
    assert command(tmp_path, "init", str(target)).returncode == 0
    result = command(tmp_path, "config", "show", "--config", str(target / "lodestone.toml"))
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["schema_version"] == 1
    assert Path(config["workspace"]["db_path"]) == target / ".lodestone/index.db"
