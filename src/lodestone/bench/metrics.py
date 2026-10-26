# SPDX-License-Identifier: Apache-2.0
"""Retrieval metrics with parent collapse, cost, and latency percentiles."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from lodestone.config import Prices
from lodestone.storage.costs import usd as priced_usd

RECALL_KS = (1, 5, 10, 20)
NDCG_K = 10


def collapse_parents(ids: Sequence[str], parent_of: Mapping[str, str] | None = None) -> list[str]:
    """Keep the first occurrence of each parent ext_id."""
    mapping = parent_of or {}
    seen: set[str] = set()
    ordered: list[str] = []
    for ident in ids:
        parent = mapping.get(ident, ident)
        if parent in seen:
            continue
        seen.add(parent)
        ordered.append(parent)
    return ordered


def recall_at(retrieved: Sequence[str], gold: Sequence[str], k: int) -> float:
    if k < 1:
        raise ValueError("k must be positive")
    if not gold:
        return 1.0
    hits = set(retrieved[:k]) & set(gold)
    return len(hits) / len(set(gold))


def mrr(retrieved: Sequence[str], gold: Sequence[str]) -> float:
    if not gold:
        return 0.0
    wanted = set(gold)
    for rank, ident in enumerate(retrieved, start=1):
        if ident in wanted:
            return 1.0 / rank
    return 0.0


def _dcg(relevances: Sequence[float], k: int) -> float:
    total = 0.0
    for rank, rel in enumerate(relevances[:k], start=1):
        total += rel / math.log2(rank + 1)
    return total


def ndcg_at(retrieved: Sequence[str], gold: Sequence[str], k: int = NDCG_K) -> float:
    if k < 1:
        raise ValueError("k must be positive")
    if not gold:
        return 0.0
    wanted = set(gold)
    rels = [1.0 if ident in wanted else 0.0 for ident in retrieved[:k]]
    ideal = [1.0] * min(len(wanted), k)
    denom = _dcg(ideal, k)
    if denom == 0.0:
        return 0.0
    return _dcg(rels, k) / denom


def retrieval_scores(
    retrieved: Sequence[str],
    gold: Sequence[str],
    *,
    parent_of: Mapping[str, str] | None = None,
) -> dict[str, float]:
    collapsed = collapse_parents(retrieved, parent_of)
    scores = {f"recall@{k}": recall_at(collapsed, gold, k) for k in RECALL_KS}
    scores["mrr"] = mrr(collapsed, gold)
    scores["ndcg@10"] = ndcg_at(collapsed, gold, NDCG_K)
    return scores


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    if p < 0 or p > 100:
        raise ValueError("percentile must be in [0, 100]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    index = (len(ordered) - 1) * (p / 100.0)
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return float(ordered[lo])
    weight = index - lo
    return float(ordered[lo] * (1.0 - weight) + ordered[hi] * weight)


def latency_summary(samples_ms: Sequence[float]) -> dict[str, float]:
    return {
        "p50_ms": percentile(samples_ms, 50),
        "p95_ms": percentile(samples_ms, 95),
        "p99_ms": percentile(samples_ms, 99),
    }


def cost_usd(in_tokens: int, out_tokens: int, prices: Prices) -> float:
    return priced_usd(in_tokens, out_tokens, prices)


def must_contain_score(answer: str, needles: Sequence[str] | None) -> float:
    if not needles:
        return 1.0
    text = answer.lower()
    hits = sum(1 for needle in needles if needle.lower() in text)
    return hits / len(needles)


def judge_score(
    answer: str,
    needles: Sequence[str] | None,
    chat: object,
) -> float:
    from lodestone.providers.chat import parse_json

    required = ", ".join(needles or [])
    complete = getattr(chat, "complete", None)
    if not callable(complete):
        return must_contain_score(answer, needles)
    result = complete(
        [
            {
                "role": "user",
                "content": (
                    "Score between 0 and 1 whether the answer covers the required facts. "
                    f"Required: {required}\nAnswer: {answer}\n"
                    'Return JSON {"score": 0.0}.'
                ),
            }
        ],
        json_mode=True,
        op="judge",
    )
    try:
        payload = parse_json(getattr(result, "text", "") or "")
    except (ValueError, TypeError):
        return must_contain_score(answer, needles)
    if isinstance(payload, dict) and "score" in payload:
        try:
            return max(0.0, min(1.0, float(payload["score"])))
        except (TypeError, ValueError):
            return must_contain_score(answer, needles)
    return must_contain_score(answer, needles)
