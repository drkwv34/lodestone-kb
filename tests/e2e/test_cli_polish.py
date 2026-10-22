# SPDX-License-Identifier: Apache-2.0
import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app
from tests.e2e.test_lexical_cli import command

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"
HELP = Path(__file__).parents[1] / "fixtures/help"
runner = CliRunner()
COMMANDS = ("search", "grep", "get", "who-knows", "recent", "stats")


def test_fr_051_cli_help_snapshots() -> None:
    for name in COMMANDS:
        result = runner.invoke(app, [name, "--help"])
        assert result.exit_code == 0, result.output
        expected = (HELP / f"{name}.txt").read_text(encoding="utf-8")
        assert result.output == expected


def test_fr_051_search_grep_get_who_knows_recent_stats(tmp_path: Path) -> None:
    shutil.copytree(CORPUS, tmp_path / "corpus")
    assert command(tmp_path, "init").returncode == 0
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(config_path.read_text().replace("sources = []", 'sources = ["wiki"]'))
    with config_path.open("a") as stream:
        stream.write(
            '\n[[sources]]\nname="wiki"\nkind="files"\npath="corpus"\nexclude=["drafts/**"]\n'
        )
    synced = command(tmp_path, "sync", "--offline")
    assert synced.returncode == 0, synced.stderr
    searched = command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--json", "--offline")
    assert searched.returncode == 0, searched.stderr
    grepped = command(tmp_path, "grep", "ERR_MANIFEST_TIMEOUT", "--json")
    assert grepped.returncode == 0, grepped.stderr
    assert json.loads(grepped.stdout)["matches"]
    got = command(tmp_path, "get", "manifest.md", "--json")
    assert got.returncode == 0, got.stderr
    who = command(tmp_path, "who-knows", "manifest", "--json")
    assert who.returncode == 0, who.stderr
    rec = command(tmp_path, "recent", "--limit", "5", "--json")
    assert rec.returncode == 0, rec.stderr
    assert json.loads(rec.stdout)["hits"]
    counted = command(tmp_path, "stats")
    assert counted.returncode == 0, counted.stderr
    stats = json.loads(counted.stdout)
    assert stats["records"] > 0
    assert stats["store_queries"] is False
    fallback = command(
        tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--rerank", "--json", "--offline"
    )
    assert fallback.returncode == 0, fallback.stderr
    assert json.loads(fallback.stdout)["notices"]
    args = ["--config", str(config_path)]
    assert runner.invoke(app, ["grep", "ERR_MANIFEST_TIMEOUT", *args]).exit_code == 0
    assert runner.invoke(app, ["who-knows", "manifest", *args]).exit_code == 0
    assert runner.invoke(app, ["recent", "--limit", "3", *args]).exit_code == 0
    assert runner.invoke(app, ["stats", *args]).exit_code == 0
    human = runner.invoke(app, ["search", "ERR_MANIFEST_TIMEOUT", "--rerank", "--offline", *args])
    assert human.exit_code == 0, human.output
