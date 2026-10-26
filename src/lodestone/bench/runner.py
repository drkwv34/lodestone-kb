# SPDX-License-Identifier: Apache-2.0
"""Run selected strategies over an evalset and collect retrieval metrics."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from lodestone.bench.cache import CachedResult, ResultCache
from lodestone.bench.evalset import CATEGORIES, EvalRow, load_evalset
from lodestone.bench.metrics import (
    judge_score,
    latency_summary,
    mean,
    must_contain_score,
    retrieval_scores,
)
from lodestone.bench.stats import bootstrap_mean, paired_diff
from lodestone.bench.strategies import DEFAULT_CONTEXT_BUDGET, build_strategy, parse_names
from lodestone.bench.synth import file_tree_hash
from lodestone.config import Prices
from lodestone.providers import Chat


def _package_version() -> str:
    try:
        return version("lodestone-kb")
    except PackageNotFoundError:
        return "0.1.0.dev0"


@dataclass
class QuestionScore:
    qid: str
    category: str
    gold_ids: list[str]
    retrieved: list[str]
    latency_ms: float
    scores: dict[str, float]
    answer: str = ""
    cached: bool = False


@dataclass
class StrategyRun:
    name: str
    status: str
    skipped_reason: str | None = None
    index_seconds: float = 0.0
    index_bytes: int = 0
    in_tokens: int = 0
    out_tokens: int = 0
    usd: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    queries: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    questions: list[QuestionScore] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    ci: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class BenchRun:
    generated_at: str
    config_hash: str
    corpus_hash: str
    versions: dict[str, str]
    embedder: str
    corpus: str
    evalset: str
    k: int
    prices: dict[str, float]
    strategies: list[StrategyRun]
    failures: list[str]
    leakage: dict[str, object] = field(default_factory=dict)
    paired: dict[str, dict[str, object]] = field(default_factory=dict)
    category_paired: dict[str, dict[str, object]] = field(default_factory=dict)
    statistics: dict[str, object] = field(default_factory=dict)


def _config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _average(rows: list[QuestionScore]) -> dict[str, float]:
    if not rows:
        return {}
    keys: set[str] = set()
    for row in rows:
        keys.update(row.scores)
    return {
        key: mean([row.scores[key] for row in rows if key in row.scores]) for key in sorted(keys)
    }


def _seed(config_hash: str) -> int:
    return int(config_hash[:8], 16)


def _attach_ci(item: StrategyRun, seed: int) -> None:
    if not item.questions:
        return
    keys: set[str] = set()
    for row in item.questions:
        keys.update(row.scores)
    for key in sorted(keys):
        values = [row.scores[key] for row in item.questions if key in row.scores]
        interval = bootstrap_mean(values, seed=seed)
        item.ci[key] = interval.dump()
        if item.questions:
            # flatten onto metrics for advise/report
            item.metrics[f"{key}_lo"] = interval.lo
            item.metrics[f"{key}_hi"] = interval.hi


def _pair_runs(
    results: list[StrategyRun], seed: int
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    by_name = {item.name: item for item in results if item.status == "ok"}
    baseline = by_name.get("classic-rag")
    paired: dict[str, dict[str, object]] = {}
    if baseline is None or not baseline.questions:
        return paired, {}
    base_ids = [row.qid for row in baseline.questions]
    base_map = {row.qid: row for row in baseline.questions}
    for name, item in by_name.items():
        if name == "classic-rag" or not item.questions:
            continue
        current = {row.qid: row for row in item.questions}
        block: dict[str, object] = {"baseline": "classic-rag"}
        for key in ("recall@10", "mrr", "ndcg@10", "correctness"):
            left = [
                current[qid].scores[key]
                for qid in base_ids
                if qid in current and key in current[qid].scores and key in base_map[qid].scores
            ]
            right = [
                base_map[qid].scores[key]
                for qid in base_ids
                if qid in current and key in current[qid].scores and key in base_map[qid].scores
            ]
            if len(left) != len(right) or not left:
                continue
            block[key] = paired_diff(left, right, seed=seed).dump()
        paired[name] = block
    category_paired: dict[str, dict[str, object]] = {}
    lexical = by_name.get("lodestone-lexical")
    if lexical is not None:
        for category in ("paraphrase", "tangent_in_long_thread"):
            left_rows = [row for row in lexical.questions if row.category == category]
            right_rows = [row for row in baseline.questions if row.category == category]
            ids = [row.qid for row in left_rows]
            right_map = {row.qid: row for row in right_rows}
            left = [row.scores.get("recall@10", 0.0) for row in left_rows if row.qid in right_map]
            right = [right_map[qid].scores.get("recall@10", 0.0) for qid in ids if qid in right_map]
            if left and len(left) == len(right):
                category_paired[category] = paired_diff(left, right, seed=seed).dump()
    return paired, category_paired


def _score_one(
    row: EvalRow,
    strategy: Any,
    k: int,
    judge: bool,
    chat: Chat | None,
) -> tuple[list[str], str, float, dict[str, float], int, int]:
    started = time.perf_counter()
    retrieved = strategy.retrieve(row.question, k)
    answer_fn = getattr(strategy, "answer", None)
    answer = str(answer_fn(row.question)) if callable(answer_fn) else ""
    latency = (time.perf_counter() - started) * 1000.0
    scores = retrieval_scores(retrieved, row.gold_ids)
    if callable(answer_fn):
        scores["correctness"] = must_contain_score(answer, row.gold_answer_must_contain)
        if judge and chat is not None:
            scores["judge"] = judge_score(answer, row.gold_answer_must_contain, chat)
    in_tokens = int(getattr(strategy, "last_in_tokens", 0) or 0)
    out_tokens = int(getattr(strategy, "last_out_tokens", 0) or 0)
    return retrieved, answer, latency, scores, in_tokens, out_tokens


def _score_strategy(
    name: str,
    corpus: Path,
    rows: list[EvalRow],
    k: int,
    table: Prices,
    work: Path,
    *,
    cache: ResultCache,
    config_hash: str,
    corpus_hash: str,
    judge: bool,
    chat: Chat | None,
    context_budget: int,
) -> StrategyRun:
    strategy = build_strategy(name, work, context_budget=context_budget, chat=chat)
    item = StrategyRun(name=name, status="ok", skipped_reason=strategy.skipped)
    try:
        stats = strategy.index(corpus)
        item.index_seconds = stats.seconds
        item.index_bytes = stats.bytes
        item.in_tokens = stats.in_tokens
        item.out_tokens = stats.out_tokens
        if strategy.skipped:
            item.status = "skipped"
            item.skipped_reason = strategy.skipped
            return item
        latencies: list[float] = []
        scored: list[QuestionScore] = []
        for row in rows:
            hit = cache.get(name, config_hash, corpus_hash, row.qid)
            if hit is not None:
                retrieved = list(hit.retrieved)
                answer = hit.answer
                latency = hit.latency_ms
                scores = dict(hit.scores)
                in_tokens, out_tokens = hit.in_tokens, hit.out_tokens
                cached = True
            else:
                retrieved, answer, latency, scores, in_tokens, out_tokens = _score_one(
                    row, strategy, k, judge, chat
                )
                cache.put(
                    CachedResult(
                        strategy=name,
                        config_hash=config_hash,
                        corpus_hash=corpus_hash,
                        qid=row.qid,
                        retrieved=list(retrieved),
                        answer=answer,
                        in_tokens=in_tokens,
                        out_tokens=out_tokens,
                        latency_ms=latency,
                        scores=dict(scores),
                    )
                )
                cached = False
            item.in_tokens += in_tokens
            item.out_tokens += out_tokens
            latencies.append(latency)
            scored.append(
                QuestionScore(
                    qid=row.qid,
                    category=row.category,
                    gold_ids=list(row.gold_ids),
                    retrieved=list(retrieved),
                    latency_ms=latency,
                    scores=scores,
                    answer=answer,
                    cached=cached,
                )
            )
        item.questions = scored
        item.queries = len(scored)
        item.metrics = _average(scored)
        item.by_category = {
            category: _average([row for row in scored if row.category == category])
            for category in CATEGORIES
        }
        summary = latency_summary(latencies)
        item.p50_ms = summary["p50_ms"]
        item.p95_ms = summary["p95_ms"]
        item.p99_ms = summary["p99_ms"]
        item.usd = (item.in_tokens * table.input + item.out_tokens * table.output) / 1_000_000
    except (OSError, ValueError, sqlite3.Error, RuntimeError, KeyError) as extra:
        item.status = "failed"
        item.failures.append(str(extra))
    finally:
        strategy.close()
    return item


def _load_leakage(evalset: Path, explicit: dict[str, object] | None) -> dict[str, object]:
    if explicit:
        return dict(explicit)
    sibling = evalset.with_name("leakage.json")
    if not sibling.is_file():
        return {"dropped": 0, "histogram": []}
    payload: object = json.loads(sibling.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {"dropped": 0, "histogram": []}


def run_bench(
    *,
    corpus: Path,
    evalset: Path,
    out: Path,
    strategies: str = "all",
    k: int = 20,
    prices: Prices | None = None,
    generated_at: str | None = None,
    judge: bool = False,
    reps: int = 1,
    context_budget: int = DEFAULT_CONTEXT_BUDGET,
    chat: Chat | None = None,
    leakage: dict[str, object] | None = None,
) -> BenchRun:
    if k < 1:
        raise ValueError("k must be positive")
    if reps < 1:
        raise ValueError("reps must be positive")
    del reps  # per-qid cache; repetitions are averaged by caller repeating qids if needed
    rows = load_evalset(evalset)
    out.mkdir(parents=True, exist_ok=True)
    names = parse_names(strategies)
    table = prices or Prices()
    stamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    corpus_hash = file_tree_hash(corpus)
    config_hash = _config_hash(
        {
            "strategies": names,
            "k": k,
            "embedder": "hash",
            "corpus_hash": corpus_hash,
            "evalset": evalset.name,
            "judge": judge,
            "context_budget": context_budget,
        }
    )
    cache = ResultCache(out / "cache.jsonl")
    results = [
        _score_strategy(
            name,
            corpus,
            rows,
            k,
            table,
            out,
            cache=cache,
            config_hash=config_hash,
            corpus_hash=corpus_hash,
            judge=judge,
            chat=chat,
            context_budget=context_budget,
        )
        for name in names
    ]
    seed = _seed(config_hash)
    for item in results:
        if item.status == "ok":
            _attach_ci(item, seed)
    paired, category_paired = _pair_runs(results, seed)
    failures = [f"{item.name}: {message}" for item in results for message in item.failures]
    run = BenchRun(
        generated_at=stamp,
        config_hash=config_hash,
        corpus_hash=corpus_hash,
        versions={"lodestone": _package_version()},
        embedder="hash",
        corpus=corpus.as_posix(),
        evalset=evalset.as_posix(),
        k=k,
        prices={"input": table.input, "output": table.output},
        strategies=results,
        failures=failures,
        leakage=_load_leakage(evalset, leakage),
        paired=paired,
        category_paired=category_paired,
        statistics={"seed": seed, "resamples": 2000},
    )
    (out / "results.json").write_text(json.dumps(asdict(run), indent=2) + "\n", encoding="utf-8")
    return run


def load_run(path: Path) -> dict[str, Any]:
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("results.json must be an object")
    return payload
