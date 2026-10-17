# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lodestone.cli import app
from lodestone.config import Config, ConfigError, load_config, redact

FIXTURES = Path(__file__).parents[1] / "fixtures" / "config"
ROOT = Path(__file__).parents[2]
runner = CliRunner()


@pytest.mark.parametrize(
    ("fixture", "path"),
    [
        ("invalid-source-kind", "sources[0].kind"),
        ("invalid-unknown-key", "workspace.unexpected"),
        ("invalid-weight-lane", "retrieval.weights.unknown_lane"),
        ("invalid-token-ratio", "chunks.chars_per_token"),
        ("invalid-schema", "schema_version"),
    ],
)
def test_fr_002_five_invalid_fixtures(fixture: str, path: str) -> None:
    config_path = FIXTURES / f"{fixture}.toml"
    with pytest.raises(ConfigError, match=path.replace("[", r"\[").replace("]", r"\]")):
        load_config(config_path)
    for command in (["config", "show"], ["doctor"]):
        result = runner.invoke(app, [*command, "--config", str(config_path)])
        assert result.exit_code == 2, result.output
        assert path in result.output


def test_fr_002_full_architecture_config_and_relative_paths(tmp_path: Path) -> None:
    architecture = (ROOT / "docs/spec/02-architecture.md").read_text()
    toml = architecture.split("```toml\n", 1)[1].split("```", 1)[0]
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(toml)
    config = load_config(config_path)
    assert config.workspace.db_path == tmp_path / ".lodestone/index.db"
    assert config.sources[0].path == tmp_path / "docs"
    assert config.sources[1].path == tmp_path / "exports/support.jsonl"
    assert config.llm is not None
    assert config.llm.prices.as_of is not None
    assert config.llm.prices.as_of.isoformat() == "2026-10-16"
    assert config.retrieval.decay["thread"].floor == 0.4
    assert config.embed.provider == "none"


def test_fr_002_example_and_independent_defaults() -> None:
    config = load_config(ROOT / "lodestone.example.toml")
    assert config.schema_version == 1
    first, second = Config(), Config()
    first.retrieval.weights["fts_raw"] = 9
    assert second.retrieval.weights["fts_raw"] == 1


@pytest.mark.parametrize(
    "content",
    [
        '[llm]\napi_key = "sensitive-value"',
        '[llm]\napi_key_env = "sensitive-value"',
        '[llm]\nbase_url = "https://user:sensitive-value@example.com/v1"',
        '[llm]\nbase_url = "https://example.com/v1?token=sensitive-value"',
        'secret = "sensitive-value"\n[invalid',
    ],
)
def test_fr_002_rejects_inline_secrets_without_echoing_values(tmp_path: Path, content: str) -> None:
    path = tmp_path / "lodestone.toml"
    path.write_text(content)
    result = runner.invoke(app, ["config", "show", "--config", str(path)])
    assert result.exit_code == 2
    assert "sensitive-value" not in result.output


def test_fr_002_unreadable_config_and_init_error(tmp_path: Path) -> None:
    missing = runner.invoke(app, ["config", "show", "--config", str(tmp_path / "missing")])
    assert missing.exit_code == 2
    (tmp_path / "lodestone.toml").write_text("schema_version = 99")
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 2
    assert "schema_version" in result.output
    assert not (tmp_path / ".lodestone/index.db").exists()


def test_fr_005_secret_redaction_preview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LODESTONE_API_KEY", "do-not-print-env-value")
    path = tmp_path / "lodestone.toml"
    path.write_text('[llm]\napi_key_env = "LODESTONE_API_KEY"')
    result = runner.invoke(app, ["config", "show", "--config", str(path)])
    assert result.exit_code == 0, result.output
    assert "[REDACTED]" in result.output
    assert "LODESTONE_API_KEY" not in result.output
    assert "do-not-print-env-value" not in result.output
    assert redact({"items": [{"AccessToken": "secret", "name": "kept"}], "secret": "hidden"}) == {
        "items": [{"AccessToken": "[REDACTED]", "name": "kept"}],
        "secret": "[REDACTED]",
    }
