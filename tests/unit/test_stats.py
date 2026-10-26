# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from lodestone.bench.stats import bootstrap_mean, paired_diff


def test_fr_075_bootstrap_known_distribution() -> None:
    values = [1.0] * 25
    first = bootstrap_mean(values, resamples=2000, seed=7)
    second = bootstrap_mean(values, resamples=2000, seed=7)
    assert first == second
    assert first.mean == 1.0
    assert first.lo == 1.0
    assert first.hi == 1.0
    mixed = [0.0, 1.0] * 20
    interval = bootstrap_mean(mixed, resamples=2000, seed=11)
    again = bootstrap_mean(mixed, resamples=2000, seed=11)
    assert interval == again
    assert interval.mean == 0.5
    assert interval.lo <= interval.mean <= interval.hi
    skewed = [0.0] * 18 + [1.0] * 2
    first_skew = bootstrap_mean(skewed, resamples=2000, seed=21)
    second_skew = bootstrap_mean(skewed, resamples=2000, seed=21)
    assert first_skew == second_skew
    assert first_skew.mean == pytest.approx(0.1)


def test_fr_075_paired_significance_flag() -> None:
    treatment = [1.0] * 16
    baseline = [0.0] * 16
    different = paired_diff(treatment, baseline, resamples=2000, seed=3)
    assert different.significant is True
    assert different.lo > 0.0
    same = paired_diff(treatment, treatment, resamples=2000, seed=3)
    assert same.significant is False
    assert same.lo <= 0.0 <= same.hi
