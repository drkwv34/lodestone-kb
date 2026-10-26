# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from lodestone.bench.evalset import load_evalset
from lodestone.bench.report import HASH_CAVEAT, write_report
from lodestone.bench.runner import run_bench
from lodestone.bench.strategies import IN_SCOPE, SKIPPED_REASONS
from lodestone.bench.synth import generate


def test_fr_073_strategies_run_offline_threads_60(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=7, threads=60)
    rows = load_evalset(corpus.evalset)
    exact = [row for row in rows if row.category == "exact_token"]
    assert exact
    run = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=tmp_path / "run",
        strategies="classic-rag,bm25-chunks,hybrid-chunks,lodestone-lexical",
        k=20,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    names = {item.name: item for item in run.strategies}
    for name in IN_SCOPE:
        item = names[name]
        assert item.status == "ok", item.failures
        assert item.questions
        assert item.index_bytes > 0
    for row in exact:
        for name in ("bm25-chunks", "lodestone-lexical"):
            scored = next(item for item in names[name].questions if item.qid == row.qid)
            assert row.gold_ids[0] in scored.retrieved
            assert not any("#w" in ident for ident in scored.retrieved)


def test_fr_073_skipped_strategies_reported(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=3, threads=6)
    run = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=tmp_path / "run",
        strategies="all",
        k=5,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    skipped = {item.name: item for item in run.strategies if item.status == "skipped"}
    assert set(skipped) == set(SKIPPED_REASONS)
    for name, reason in SKIPPED_REASONS.items():
        assert skipped[name].skipped_reason == reason
    markdown_path, _json_path = write_report(tmp_path / "run")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert HASH_CAVEAT in markdown
    for name in SKIPPED_REASONS:
        assert name in markdown
        assert "skipped" in markdown
