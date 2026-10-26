# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from lodestone.bench.metrics import (
    collapse_parents,
    cost_usd,
    judge_score,
    latency_summary,
    mean,
    mrr,
    must_contain_score,
    ndcg_at,
    percentile,
    recall_at,
    retrieval_scores,
)
from lodestone.config import Prices
from lodestone.providers.fake import FakeLLM


def test_fr_074_metric_goldens() -> None:
    # Hand-computed on retrieved=[c, a, b], gold={a, b}:
    # recall@1 = |{c} ∩ gold| / 2 = 0
    # recall@5 = 2 / 2 = 1
    # MRR = 1/2 = 0.5 (first relevant at rank 2)
    # DCG@10 = 1/log2(3) + 1/log2(4) = 0.6309297535714575 + 0.5 = 1.1309297535714575
    # IDCG@10 = 1/log2(2) + 1/log2(3) = 1.6309297535714575
    # nDCG@10 = 1.1309297535714575 / 1.6309297535714575 = 0.6934264036172708
    retrieved = ["c", "a", "b"]
    gold = ["a", "b"]
    assert recall_at(retrieved, gold, 1) == 0.0
    assert recall_at(retrieved, gold, 5) == 1.0
    assert recall_at(retrieved, gold, 10) == 1.0
    assert recall_at(retrieved, gold, 20) == 1.0
    assert mrr(retrieved, gold) == 0.5
    assert ndcg_at(retrieved, gold, 10) == pytest.approx(0.6934264036172708)
    scores = retrieval_scores(retrieved, gold)
    assert scores["recall@1"] == 0.0
    assert scores["mrr"] == 0.5
    assert scores["ndcg@10"] == pytest.approx(0.6934264036172708)
    assert recall_at([], ["a"], 5) == 0.0
    assert mrr(["x"], ["a"]) == 0.0
    assert recall_at(["x"], [], 5) == 1.0
    assert mrr(["x"], []) == 0.0
    assert ndcg_at(["x"], [], 10) == 0.0
    lat = latency_summary([10.0, 20.0, 30.0, 40.0])
    # n=4, p50 index=1.5 → 25; p95 index=2.85 → 38.5
    assert lat["p50_ms"] == pytest.approx(25.0)
    assert lat["p95_ms"] == pytest.approx(38.5)
    assert cost_usd(1_000_000, 0, Prices(input=2.0, output=0.0)) == 2.0
    with pytest.raises(ValueError, match="k must be positive"):
        recall_at(["a"], ["a"], 0)
    assert mean([]) == 0.0
    assert percentile([], 50) == 0.0
    assert percentile([7.0], 95) == 7.0
    with pytest.raises(ValueError, match="percentile"):
        percentile([1.0], -1)


def test_fr_074_parent_collapse() -> None:
    parent_of = {"p1#w0": "p1", "p2#w1": "p2", "p1#w2": "p1"}
    collapsed = collapse_parents(["p1#w0", "p2#w1", "p1#w2"], parent_of)
    assert collapsed == ["p1", "p2"]
    scores = retrieval_scores(["p1#w0", "p2#w1", "p1#w2"], ["p1"], parent_of=parent_of)
    assert scores["recall@1"] == 1.0
    assert scores["mrr"] == 1.0
    assert collapse_parents(["a", "a", "b"]) == ["a", "b"]


def test_fr_074_must_contain_correctness() -> None:
    assert must_contain_score("Set prefetch to four on NFS.", ["prefetch to four"]) == 1.0
    assert must_contain_score("wrong", ["prefetch to four"]) == 0.0
    assert must_contain_score("one two", ["one", "missing"]) == 0.5
    assert must_contain_score("anything", None) == 1.0
    assert must_contain_score("anything", []) == 1.0


def test_fr_074_optional_judge() -> None:
    chat = FakeLLM(script=['{"score": 0.75}'])
    score = judge_score("Set prefetch to four.", ["prefetch to four"], chat)
    assert score == 0.75
    fallback = FakeLLM(script=["not-json"])
    assert judge_score("Set prefetch to four.", ["prefetch to four"], fallback) == 1.0
