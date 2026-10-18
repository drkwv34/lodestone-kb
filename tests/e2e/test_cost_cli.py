# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app

runner = CliRunner()


def test_fr_026_fr_063_cost_and_fake_provider_resync(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "note.md").write_text("# Note\nstable unique_token body\n", encoding="utf-8")
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0, result.output
    config = tmp_path / "lodestone.toml"
    config.write_text(config.read_text().replace("sources = []", 'sources = ["docs"]'))
    with config.open("a", encoding="utf-8") as stream:
        stream.write('\n[[sources]]\nname="docs"\nkind="files"\npath="docs"\n')
    first = runner.invoke(app, ["sync", "--provider", "fake", "--config", str(config)])
    assert first.exit_code == 0, first.output
    payload = json.loads(first.stdout)
    assert payload["llm_calls"] >= 1
    assert payload["processed"] >= 1
    second = runner.invoke(app, ["sync", "--provider", "fake", "--config", str(config)])
    assert second.exit_code == 0, second.output
    again = json.loads(second.stdout)
    assert again["llm_calls"] == 0
    assert again["processed"] == 0
    cost = runner.invoke(app, ["cost", "--config", str(config)])
    assert cost.exit_code == 0, cost.output
    summary = json.loads(cost.stdout)
    assert summary["total"]["calls"] == payload["llm_calls"]
    got = runner.invoke(app, ["get", "note.md", "--json", "--config", str(config)])
    assert got.exit_code == 0, got.output
    view = json.loads(got.stdout)
    assert view["raw_text"]
    assert view["card"] is not None
    assert view["card"]["char_spans"] or view["card"]["source_message_ids"]
    human = runner.invoke(app, ["get", "note.md", "--config", str(config)])
    assert human.exit_code == 0, human.output
    assert "stable unique_token body" in human.stdout
    missing = runner.invoke(app, ["get", "absent.md", "--config", str(config)])
    assert missing.exit_code == 1
    absent_llm = runner.invoke(app, ["sync", "--provider", "config", "--config", str(config)])
    assert absent_llm.exit_code == 2
    bad = runner.invoke(app, ["sync", "--provider", "nope", "--config", str(config)])
    assert bad.exit_code == 2
