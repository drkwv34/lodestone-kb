# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app
from tests.e2e.test_lexical_cli import command

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"


def test_fr_033_fr_062_fr_083_offline_search_reindex_and_disabled_notice(tmp_path: Path) -> None:
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
    assert json.loads(synced.stdout)["processed"] >= 1
    found = command(
        tmp_path,
        "search",
        "ERR_MANIFEST_TIMEOUT",
        "--lane",
        "vec_card",
        "--offline",
        "--explain",
        "--json",
    )
    assert found.returncode == 0, found.stderr
    payload = json.loads(found.stdout)
    assert payload["lane"] == "vec_card"
    assert payload["hits"]
    assert payload["explain"][0]["lane"] == "vec_card"
    before = command(tmp_path, "reindex", "--lanes", "vec", "--offline")
    assert before.returncode == 0, before.stderr
    counts = json.loads(before.stdout)
    assert counts["before"] == counts["after"]
    disabled = command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--lane", "vec_card", "--json")
    assert disabled.returncode == 0, disabled.stderr
    notice = json.loads(disabled.stdout)
    assert notice["hits"] == []
    assert any("skipped" in item for item in notice["notices"])
    runner = CliRunner()
    human = runner.invoke(
        app,
        [
            "search",
            "ERR_MANIFEST_TIMEOUT",
            "--config",
            str(config_path),
            "--lane",
            "vec_card",
        ],
    )
    assert human.exit_code == 0
    assert "notice:" in human.output
    blocked = runner.invoke(app, ["reindex", "--lanes", "vec", "--config", str(config_path)])
    assert blocked.exit_code == 2
    assert "embeddings are disabled" in blocked.output
    unknown = runner.invoke(app, ["reindex", "--lanes", "fts", "--config", str(config_path)])
    assert unknown.exit_code == 2
