# SPDX-License-Identifier: Apache-2.0
"""Weighted reciprocal rank fusion with k=60 (ADR-004)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LaneContribution:
    rank: int
    raw_score: float
    contribution: float


@dataclass(frozen=True)
class FusedScore:
    rrf: float
    lanes: dict[str, LaneContribution]


def rrf(
    lists: dict[str, list[int]],
    weights: dict[str, float] | None = None,
    k: int = 60,
    raw_scores: dict[str, dict[int, float]] | None = None,
) -> dict[int, FusedScore]:
    """score(d) = sum_l w_l / (k + rank_l(d)) with ranks starting at 1."""
    if k < 1:
        raise ValueError("k must be positive")
    configured = weights or {}
    scores = raw_scores or {}
    per_id: dict[int, dict[str, LaneContribution]] = {}
    for lane, ranked in lists.items():
        weight = float(configured.get(lane, 1.0))
        lane_scores = scores.get(lane, {})
        seen: set[int] = set()
        for rank, record_id in enumerate(ranked, start=1):
            if record_id in seen:
                continue
            seen.add(record_id)
            per_id.setdefault(record_id, {})[lane] = LaneContribution(
                rank=rank,
                raw_score=float(lane_scores.get(record_id, 0.0)),
                contribution=weight / (k + rank),
            )
    return {
        record_id: FusedScore(
            rrf=sum(item.contribution for item in lanes.values()),
            lanes=lanes,
        )
        for record_id, lanes in per_id.items()
    }
