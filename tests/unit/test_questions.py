# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import pytest

from lodestone.bench.questions import (
    dump_evalset,
    generate_from_config,
    generate_questions,
    leakage_histogram,
    leakage_score,
)
from lodestone.bench.strategies.lodestone import lodestone_lexical
from lodestone.bench.synth import generate
from lodestone.config import load_config
from lodestone.providers.fake import FakeLLM
from lodestone.tokenize import tokenize


def test_fr_072_leakage_filter() -> None:
    gold = "CKPT_PREFETCH equals four on NFS mounts"
    quoted = gold
    paraphrased = "How is restore tuned for network mounts?"
    assert leakage_score(quoted, gold) == 1.0
    overlap = leakage_score(paraphrased, gold)
    assert overlap < 0.5
    assert set(tokenize(paraphrased))
    chat = FakeLLM(
        script=[
            json.dumps(
                [
                    {"question": paraphrased, "category": "paraphrase"},
                    {"question": quoted, "category": "exact_token"},
                ]
            )
        ]
    )
    records = [
        {
            "ext_id": "docs/a.md",
            "source": "docs",
            "kind": "doc",
            "title": "prefetch",
            "text": gold,
        }
    ]
    generated = generate_questions(records, n=1, chat=chat, leakage_max=0.5, seed=1)
    assert generated.leakage.dropped == 1
    assert generated.leakage.kept == 1
    assert len(generated.rows) == 1
    assert generated.rows[0].question == paraphrased
    assert generated.leakage.histogram
    counts = sum(int(row["count"]) for row in generated.leakage.histogram)
    assert counts == 2
    assert any(int(row["count"]) for row in leakage_histogram([0.0, 1.0]))
    assert leakage_score("", "") == 0.0
    assert dump_evalset(generated.rows).endswith("\n")
    with pytest.raises(ValueError, match="n must be positive"):
        generate_questions(records, n=0, chat=chat, seed=1)


def test_fr_072_generate_from_workspace(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=1, threads=2)
    workspace = lodestone_lexical(tmp_path / "ws")
    workspace.index(corpus.directory)
    config = load_config(workspace.config_path)
    chat = FakeLLM(
        script=[
            json.dumps([{"question": "What happened here?", "category": "paraphrase"}]),
            json.dumps([{"question": "What happened here?", "category": "paraphrase"}]),
        ]
    )
    generated = generate_from_config(config, n=2, chat=chat, leakage_max=0.5, seed=1)
    assert generated.leakage.histogram
    assert generated.leakage.dropped + generated.leakage.kept >= 1
