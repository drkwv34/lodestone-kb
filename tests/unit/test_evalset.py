# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import pytest

from lodestone.bench.evalset import EvalsetError, load_evalset
from lodestone.bench.schema import load_schema


def _write(path: Path, rows: list[object]) -> Path:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def test_fr_070_evalset_validates(tmp_path: Path) -> None:
    schema = load_schema("evalset.v1.json")
    assert schema["title"] == "evalset.v1"
    path = _write(
        tmp_path / "evalset.jsonl",
        [
            {
                "qid": "q1",
                "question": "What raises ERR_SYNTH_0001?",
                "gold_ids": ["docs/exact_0001.md"],
                "category": "exact_token",
                "gold_answer_must_contain": ["manifest"],
                "source_hint": "docs/exact_0001.md",
            }
        ],
    )
    rows = load_evalset(path)
    assert rows[0].qid == "q1"
    assert rows[0].gold_ids == ["docs/exact_0001.md"]
    assert rows[0].category == "exact_token"


def test_fr_070_invalid_rows_report_line_numbers(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps(
            {
                "qid": "q1",
                "question": "ok",
                "gold_ids": ["a"],
                "category": "exact_token",
            }
        )
        + "\n{not json}\n",
        encoding="utf-8",
    )
    with pytest.raises(EvalsetError, match="line 2") as invalid_json:
        load_evalset(path)
    assert invalid_json.value.line == 2
    missing = _write(
        tmp_path / "missing.jsonl",
        [{"question": "no qid", "gold_ids": [], "category": "unanswerable"}],
    )
    with pytest.raises(EvalsetError, match="line 1") as missing_qid:
        load_evalset(missing)
    assert missing_qid.value.line == 1
    unknown = _write(
        tmp_path / "unknown.jsonl",
        [{"qid": "q", "question": "q", "gold_ids": [], "category": "not-a-category"}],
    )
    with pytest.raises(EvalsetError, match="line 1"):
        load_evalset(unknown)
    extra = _write(
        tmp_path / "extra.jsonl",
        [
            {
                "qid": "q",
                "question": "q",
                "gold_ids": ["a"],
                "category": "exact_token",
                "nope": True,
            }
        ],
    )
    with pytest.raises(EvalsetError, match="line 1"):
        load_evalset(extra)
    empty_gold = _write(
        tmp_path / "empty_gold.jsonl",
        [{"qid": "q", "question": "q", "gold_ids": [""], "category": "exact_token"}],
    )
    with pytest.raises(EvalsetError, match="line 1"):
        load_evalset(empty_gold)
    blank = tmp_path / "blank.jsonl"
    blank.write_text("\n", encoding="utf-8")
    with pytest.raises(EvalsetError, match="empty"):
        load_evalset(blank)
    array_row = tmp_path / "array.jsonl"
    array_row.write_text("[1]\n", encoding="utf-8")
    with pytest.raises(EvalsetError, match="object"):
        load_evalset(array_row)
