# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import click
from typer.testing import CliRunner

from lodestone.cli import app
from tests.e2e.test_lexical_cli import command
from tests.helpers import synced_workspace

HELP = Path(__file__).parents[1] / "fixtures/help"
runner = CliRunner(env={"NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"})


def test_fr_051_ask_and_mcp_commands(tmp_path: Path) -> None:
    for name in ("ask", "mcp"):
        result = runner.invoke(app, [name, "--help"], color=False)
        assert result.exit_code == 0, result.output
        expected = (HELP / f"{name}.txt").read_text(encoding="utf-8")
        assert click.unstyle(result.output) == expected
    config_path = synced_workspace(tmp_path)
    asked = command(
        tmp_path,
        "ask",
        "Why does restore stall?",
        "--provider",
        "fake",
        "--offline",
        "--json",
        "--max-rounds",
        "1",
    )
    assert asked.returncode == 0, asked.stderr
    payload = json.loads(asked.stdout)
    invoked = runner.invoke(
        app,
        [
            "ask",
            "Why does restore stall?",
            "--provider",
            "fake",
            "--offline",
            "--json",
            "--max-rounds",
            "1",
            "--config",
            str(config_path),
        ],
    )
    assert invoked.exit_code == 0, invoked.output
    invoked_payload = json.loads(invoked.stdout)
    assert "citations" in invoked_payload
    assert "insufficient_evidence" in invoked_payload
    assert "text" in payload
    assert "insufficient_evidence" in payload
    assert "citations" in payload
    mcp_help = command(tmp_path, "mcp", "--help")
    assert mcp_help.returncode == 0, mcp_help.stderr
