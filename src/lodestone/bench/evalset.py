# SPDX-License-Identifier: Apache-2.0
"""evalset.v1 JSONL loader with 1-based line numbers on invalid rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from lodestone.bench.schema import load_schema

CATEGORIES = (
    "exact_token",
    "paraphrase",
    "stale_vs_fresh",
    "tangent_in_long_thread",
    "multi_source",
    "unanswerable",
)
Category = Literal[
    "exact_token",
    "paraphrase",
    "stale_vs_fresh",
    "tangent_in_long_thread",
    "multi_source",
    "unanswerable",
]


class EvalsetError(ValueError):
    """Invalid evalset row; `line` is 1-based."""

    def __init__(self, line: int, message: str) -> None:
        self.line = line
        super().__init__(f"evalset line {line}: {message}")


class EvalRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qid: str = Field(min_length=1)
    question: str = Field(min_length=1)
    gold_ids: list[str]
    category: Category
    gold_answer_must_contain: list[str] | None = None
    source_hint: str | None = None

    def dump(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "qid": self.qid,
            "question": self.question,
            "gold_ids": list(self.gold_ids),
            "category": self.category,
        }
        if self.gold_answer_must_contain:
            payload["gold_answer_must_contain"] = list(self.gold_answer_must_contain)
        if self.source_hint:
            payload["source_hint"] = self.source_hint
        return payload


def _check_schema(row: dict[str, Any], spec: dict[str, Any], line: int) -> None:
    required = spec.get("required", [])
    properties = spec.get("properties", {})
    for key in required:
        if key not in row:
            raise EvalsetError(line, f"missing field {key!r}")
    if spec.get("additionalProperties") is False:
        extra = set(row) - set(properties)
        if extra:
            raise EvalsetError(line, f"extra fields: {sorted(extra)}")


def load_evalset(path: Path) -> list[EvalRow]:
    spec = load_schema("evalset.v1.json")
    rows: list[EvalRow] = []
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    for line, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise EvalsetError(line, f"invalid JSON ({exc.msg})") from exc
        if not isinstance(payload, dict):
            raise EvalsetError(line, "row must be a JSON object")
        _check_schema(payload, spec, line)
        try:
            rows.append(EvalRow.model_validate(payload))
        except ValidationError as exc:
            raise EvalsetError(line, exc.errors()[0]["msg"]) from exc
        if any(not ident for ident in rows[-1].gold_ids):
            raise EvalsetError(line, "gold_ids must not contain empty strings")
    if not rows:
        raise EvalsetError(1, "evalset is empty")
    return rows
