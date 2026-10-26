# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

from lodestone.bench.report import write_report
from lodestone.bench.runner import run_bench
from lodestone.bench.synth import generate


def test_fr_073_full_context_skipped_too_large(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=5, threads=2)
    run = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=tmp_path / "run",
        strategies="full-context",
        k=5,
        context_budget=1,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    item = run.strategies[0]
    assert item.status == "skipped"
    assert item.skipped_reason == "too_large"
    markdown_path, _json_path = write_report(tmp_path / "run")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "full-context" in markdown
    assert "too_large" in markdown
    assert "skipped" in markdown
