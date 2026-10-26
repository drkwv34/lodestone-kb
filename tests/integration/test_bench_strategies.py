# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from lodestone.bench.evalset import load_evalset
from lodestone.bench.report import HASH_CAVEAT, write_report
from lodestone.bench.runner import run_bench
from lodestone.bench.strategies import ALL_STRATEGIES, IN_SCOPE
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
        strategies="bm25-chunks,full-context",
        k=5,
        context_budget=1,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    names = [item.name for item in run.strategies]
    assert names == ["bm25-chunks", "full-context"]
    skipped = {item.name: item for item in run.strategies if item.status == "skipped"}
    assert "full-context" in skipped
    assert skipped["full-context"].skipped_reason == "too_large"
    markdown_path, _json_path = write_report(tmp_path / "run")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert HASH_CAVEAT in markdown
    assert "full-context" in markdown
    assert "too_large" in markdown
    assert "bm25-chunks" in markdown


def test_fr_073_remaining_strategies_run_offline(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=8, threads=6)
    run = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=tmp_path / "run",
        strategies="lodestone-hybrid,lodestone-rerank,agentic-ask,grep-agent,full-context",
        k=5,
        context_budget=1_000_000,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    names = {item.name: item for item in run.strategies}
    remaining = (
        "lodestone-hybrid",
        "lodestone-rerank",
        "agentic-ask",
        "grep-agent",
        "full-context",
    )
    for name in remaining:
        item = names[name]
        assert item.status == "ok", item.failures
        assert item.questions
    assert set(ALL_STRATEGIES) >= set(remaining)
