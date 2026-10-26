# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from lodestone.bench.advise import (
    R1_VERDICT,
    R2_VERDICT,
    R3_VERDICT,
    R4_VERDICT,
    advise,
)


def test_fr_077_advise_r1() -> None:
    report = {
        "strategies": [
            {"name": "lodestone-lexical", "status": "ok", "recall@10": 0.80},
            {"name": "lodestone-hybrid", "status": "ok", "recall@10": 0.82},
            {"name": "classic-rag", "status": "ok", "recall@10": 0.40},
        ],
        "paired": {
            "lodestone-lexical": {"recall@10": {"lo": -0.04, "hi": 0.03, "significant": False}}
        },
    }
    advice = advise(report)
    assert advice.rule == "R1"
    assert advice.verdict == R1_VERDICT
    assert any("recall@10" in line for line in advice.evidence)


def test_fr_077_advise_r2() -> None:
    report = {
        "strategies": [
            {
                "name": "lodestone-lexical",
                "status": "ok",
                "recall@10": 0.20,
                "correctness": 0.40,
            },
            {
                "name": "classic-rag",
                "status": "ok",
                "recall@10": 0.90,
                "correctness": 0.50,
                "usd": 1.0,
                "queries": 1,
            },
            {
                "name": "full-context",
                "status": "ok",
                "recall@10": 1.0,
                "correctness": 0.95,
                "correctness_lo": 0.90,
                "correctness_hi": 0.99,
                "usd": 2.5,
                "queries": 1,
            },
        ],
        "cost_latency": [
            {"strategy": "classic-rag", "usd": 1.0, "queries": 1},
            {"strategy": "full-context", "usd": 2.5, "queries": 1},
        ],
        "paired": {
            "lodestone-lexical": {"recall@10": {"lo": -0.9, "hi": -0.5, "significant": True}}
        },
    }
    advice = advise(report)
    assert advice.rule == "R2"
    assert advice.verdict == R2_VERDICT
    assert any("full-context" in line for line in advice.evidence)


def test_fr_077_advise_r3() -> None:
    report = {
        "strategies": [
            {"name": "lodestone-lexical", "status": "ok", "recall@10": 0.20},
            {"name": "classic-rag", "status": "ok", "recall@10": 0.90},
            {"name": "full-context", "status": "skipped", "skipped_reason": "too_large"},
        ],
        "categories": [
            {"strategy": "lodestone-lexical", "category": "paraphrase", "recall@10": 0.85},
            {"strategy": "classic-rag", "category": "paraphrase", "recall@10": 0.20},
        ],
        "category_paired": {"paraphrase": {"lo": 0.2, "hi": 0.8, "significant": True}},
        "paired": {
            "lodestone-lexical": {"recall@10": {"lo": -0.9, "hi": -0.4, "significant": True}}
        },
    }
    advice = advise(report)
    assert advice.rule == "R3"
    assert advice.verdict == R3_VERDICT
    assert any("paraphrase" in line for line in advice.evidence)


def test_fr_077_advise_r4() -> None:
    report = {
        "strategies": [
            {"name": "lodestone-lexical", "status": "ok", "recall@10": 0.20},
            {"name": "classic-rag", "status": "ok", "recall@10": 0.90},
            {"name": "full-context", "status": "skipped", "skipped_reason": "too_large"},
        ],
        "categories": [
            {"strategy": "lodestone-lexical", "category": "paraphrase", "recall@10": 0.10},
            {"strategy": "classic-rag", "category": "paraphrase", "recall@10": 0.80},
        ],
        "category_paired": {"paraphrase": {"lo": -0.9, "hi": -0.2, "significant": True}},
        "paired": {
            "lodestone-lexical": {"recall@10": {"lo": -0.9, "hi": -0.4, "significant": True}}
        },
    }
    advice = advise(report)
    assert advice.rule == "R4"
    assert advice.verdict == R4_VERDICT
    assert advice.evidence
