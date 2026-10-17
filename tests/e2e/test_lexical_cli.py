# SPDX-License-Identifier: Apache-2.0
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"


def command(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["lodestone", *args],  # noqa: S607
        cwd=directory,
        text=True,
        capture_output=True,
        check=False,
    )


def test_fr_010_fr_030_fr_041_sync_search_smoke(tmp_path: Path) -> None:
    shutil.copytree(CORPUS, tmp_path / "corpus")
    assert command(tmp_path, "init").returncode == 0
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(config_path.read_text().replace("sources = []", 'sources = ["wiki"]'))
    with config_path.open("a") as stream:
        stream.write(
            '\n[retrieval]\nrare_df_ratio=0.3\n[[sources]]\nname="wiki"\nkind="files"\n'
            'path="corpus"\nexclude=["drafts/**"]\n'
        )
    first = command(tmp_path, "sync")
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)["processed"] == 4
    second = command(tmp_path, "sync")
    assert json.loads(second.stdout)["processed"] == 0
    human = command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--kind", "doc")
    assert human.returncode == 0, human.stderr
    assert "1. wiki/manifest.md [doc] (fts_raw," in human.stdout
    result = command(
        tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--source", "wiki", "--kind", "doc", "--json"
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["lane"] == "fts_raw"
    assert output["hits"][0]["ext_id"] == "manifest.md"
    assert output["hits"][0]["source"] == "wiki"
    assert output["hits"][0]["kind"] == "doc"
    rare = command(
        tmp_path,
        "search",
        "ERR_MANIFEST_TIMEOUT manifest",
        "--lane",
        "fts_rare",
        "--kind",
        "doc",
        "--json",
    )
    assert rare.returncode == 0, rare.stderr
    assert [hit["ext_id"] for hit in json.loads(rare.stdout)["hits"]] == ["manifest.md"]
    assert command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--source", "other").returncode == 2
    assert command(tmp_path, "search", "test", "--lane", "fts_card").returncode == 2


def test_fr_010_fr_030_cli_errors_and_readonly_search(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "lodestone.toml"
    config.write_text("schema_version=1\n")
    missing = runner.invoke(app, ["search", "needle", "--config", str(config)])
    assert missing.exit_code == 1
    assert "Search error" in missing.output
    assert not (tmp_path / ".lodestone").exists()
    invalid = runner.invoke(app, ["sync", "--config", str(tmp_path / "absent.toml")])
    assert invalid.exit_code == 2
    assert "Configuration error" in invalid.output
    config.write_text('[[sources]]\nname="x"\nkind="files"\npath="missing"\n')
    unavailable = runner.invoke(app, ["sync", "--config", str(config)])
    assert unavailable.exit_code == 1
    config.write_text('[[sources]]\nname="x"\nkind="files"\npath="."\ninclude=["../*.txt"]\n')
    escaped = runner.invoke(app, ["sync", "--config", str(config)])
    assert escaped.exit_code == 2
    assert "patterns" in escaped.output
    with sqlite3.connect(tmp_path / ".lodestone/index.db") as connection:
        connection.execute("PRAGMA user_version=1")
    migration = runner.invoke(app, ["search", "needle", "--config", str(config)])
    assert migration.exit_code == 1
    assert "run lodestone init" in migration.output
