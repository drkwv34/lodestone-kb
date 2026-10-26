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

from lodestone.bench.evalset import CATEGORIES, EvalRow, load_evalset
from lodestone.bench.metrics import latency_summary, mean, retrieval_scores
from lodestone.bench.strategies import build_strategy, parse_names
from lodestone.bench.synth import file_tree_hash
from lodestone.config import Prices


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
    metrics: dict[str, float] = field(default_factory=dict)
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    questions: list[QuestionScore] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


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


def _config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _average(rows: list[QuestionScore]) -> dict[str, float]:
    if not rows:
        return {}
    keys = rows[0].scores.keys()
    return {key: mean([row.scores[key] for row in rows]) for key in keys}


def _score_strategy(
    name: str, corpus: Path, rows: list[EvalRow], k: int, table: Prices, work: Path
) -> StrategyRun:
    strategy = build_strategy(name, work)
    item = StrategyRun(name=name, status="ok", skipped_reason=strategy.skipped)
    try:
        if strategy.skipped:
            item.status = "skipped"
            return item
        stats = strategy.index(corpus)
        item.index_seconds = stats.seconds
        item.index_bytes = stats.bytes
        item.in_tokens = stats.in_tokens
        item.out_tokens = stats.out_tokens
        item.usd = (stats.in_tokens * table.input + stats.out_tokens * table.output) / 1_000_000
        latencies: list[float] = []
        scored: list[QuestionScore] = []
        for row in rows:
            started = time.perf_counter()
            retrieved = strategy.retrieve(row.question, k)
            latencies.append((time.perf_counter() - started) * 1000.0)
            scored.append(
                QuestionScore(
                    qid=row.qid,
                    category=row.category,
                    gold_ids=list(row.gold_ids),
                    retrieved=list(retrieved),
                    latency_ms=latencies[-1],
                    scores=retrieval_scores(retrieved, row.gold_ids),
                )
            )
        item.questions = scored
        item.metrics = _average(scored)
        item.by_category = {
            category: _average([row for row in scored if row.category == category])
            for category in CATEGORIES
        }
        latency = latency_summary(latencies)
        item.p50_ms = latency["p50_ms"]
        item.p95_ms = latency["p95_ms"]
        item.p99_ms = latency["p99_ms"]
    except (OSError, ValueError, sqlite3.Error, RuntimeError, KeyError) as extra:
        item.status = "failed"
        item.failures.append(str(extra))
    finally:
        strategy.close()
    return item


def run_bench(
    *,
    corpus: Path,
    evalset: Path,
    out: Path,
    strategies: str = "all",
    k: int = 20,
    prices: Prices | None = None,
    generated_at: str | None = None,
) -> BenchRun:
    if k < 1:
        raise ValueError("k must be positive")
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
        }
    )
    results = [_score_strategy(name, corpus, rows, k, table, out) for name in names]
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
    )
    (out / "results.json").write_text(json.dumps(asdict(run), indent=2) + "\n", encoding="utf-8")
    return run


def load_run(path: Path) -> dict[str, Any]:
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("results.json must be an object")
    return payload
