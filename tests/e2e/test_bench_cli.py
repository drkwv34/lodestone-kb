# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app

runner = CliRunner(env={"NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"})


def test_fr_051_bench_commands(tmp_path: Path) -> None:
    for name in ("synth", "run", "report", "generate", "advise"):
        result = runner.invoke(app, ["bench", name, "--help"], color=False)
        assert result.exit_code == 0, result.output
    synth = runner.invoke(
        app,
        ["bench", "synth", "--seed", "2", "--threads", "6", "--out", str(tmp_path / "corpus")],
    )
    assert synth.exit_code == 0, synth.output
    assert "corpus_hash" in synth.output
    out = tmp_path / "run"
    ran = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--corpus",
            str(tmp_path / "corpus"),
            "--out",
            str(out),
            "--strategies",
            "bm25-chunks",
            "--k",
            "5",
        ],
    )
    assert ran.exit_code == 0, ran.output
    assert (out / "report.md").is_file()
    rendered = runner.invoke(app, ["bench", "report", str(out)])
    assert rendered.exit_code == 0, rendered.output
    payload = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "report.v1"
    assert payload["embedder"] == "hash"
    advised = runner.invoke(app, ["bench", "advise", str(out)])
    assert advised.exit_code == 0, advised.output
    assert "verdict:" in advised.output
    unknown = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--corpus",
            str(tmp_path / "corpus"),
            "--out",
            str(tmp_path / "bad"),
            "--strategies",
            "not-a-strategy",
        ],
    )
    assert unknown.exit_code == 2
    assert "unknown strategy" in unknown.output


def test_fr_070_run_validates_evalset(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "evalset.jsonl").write_text("{bad json}\n", encoding="utf-8")
    result = runner.invoke(
        app,
        ["bench", "run", "--corpus", str(corpus), "--out", str(tmp_path / "run")],
    )
    assert result.exit_code == 2
    assert "line 1" in result.output
