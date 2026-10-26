# SPDX-License-Identifier: Apache-2.0
"""Seeded percentile bootstrap CIs and paired differences for bench metrics."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_RESAMPLES = 2000
DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class Interval:
    mean: float
    lo: float
    hi: float
    significant: bool | None = None

    def dump(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "mean": self.mean,
            "lo": self.lo,
            "hi": self.hi,
        }
        if self.significant is not None:
            payload["significant"] = self.significant
        return payload


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def bootstrap_mean(
    values: Sequence[float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int,
    alpha: float = DEFAULT_ALPHA,
) -> Interval:
    if resamples < 1:
        raise ValueError("resamples must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    observed = _mean(values)
    if not values:
        return Interval(mean=0.0, lo=0.0, hi=0.0)
    rng = random.Random(seed)  # noqa: S311 - seeded bootstrap, not cryptography
    n = len(values)
    means = []
    for _ in range(resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_index = int((alpha / 2) * resamples)
    hi_index = min(resamples - 1, int((1 - alpha / 2) * resamples) - 1)
    if hi_index < lo_index:
        hi_index = lo_index
    return Interval(mean=observed, lo=means[lo_index], hi=means[hi_index])


def paired_diff(
    treatment: Sequence[float],
    baseline: Sequence[float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int,
    alpha: float = DEFAULT_ALPHA,
) -> Interval:
    if len(treatment) != len(baseline):
        raise ValueError("paired series must have the same length")
    diffs = [left - right for left, right in zip(treatment, baseline, strict=True)]
    interval = bootstrap_mean(diffs, resamples=resamples, seed=seed, alpha=alpha)
    includes_zero = interval.lo <= 0.0 <= interval.hi
    return Interval(
        mean=interval.mean,
        lo=interval.lo,
        hi=interval.hi,
        significant=not includes_zero,
    )
