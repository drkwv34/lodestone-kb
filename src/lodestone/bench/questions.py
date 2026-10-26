# SPDX-License-Identifier: Apache-2.0
"""Generate eval questions from workspace records and filter lexical leakage."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Any

from lodestone.bench.evalset import CATEGORIES, Category, EvalRow
from lodestone.config import Config
from lodestone.providers import Chat, FakeLLM, parse_json
from lodestone.storage.db import open_readonly
from lodestone.tokenize import tokenize

DEFAULT_LEAKAGE_MAX = 0.5
QUESTIONS_PER_RECORD = (1, 3)
BINS = 10

PROMPT = (
    "Write 1 to 3 evaluation questions a user would ask about this record. "
    "Do not copy phrases from the record. Return a JSON array of objects with "
    f"keys question and category (one of {', '.join(CATEGORIES)}).\n"
    "source={source} kind={kind} title={title}\n"
    "Record text:\n{text}\n"
)


@dataclass
class LeakageStats:
    dropped: int = 0
    kept: int = 0
    scores: list[float] = field(default_factory=list)
    histogram: list[dict[str, float | int]] = field(default_factory=list)

    def dump(self) -> dict[str, object]:
        return {
            "dropped": self.dropped,
            "kept": self.kept,
            "histogram": list(self.histogram),
        }


@dataclass
class GeneratedQuestions:
    rows: list[EvalRow]
    leakage: LeakageStats


def leakage_score(question: str, gold: str) -> float:
    left = set(tokenize(question))
    right = set(tokenize(gold))
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def leakage_histogram(scores: list[float], bins: int = BINS) -> list[dict[str, float | int]]:
    counts = [0] * bins
    for score in scores:
        clamped = min(1.0, max(0.0, score))
        index = bins - 1 if clamped >= 1.0 else min(bins - 1, int(clamped * bins))
        counts[index] += 1
    return [
        {"lo": index / bins, "hi": (index + 1) / bins, "count": counts[index]}
        for index in range(bins)
    ]


def load_parent_records(config: Config) -> list[dict[str, str]]:
    connection = open_readonly(config.workspace.db_path)
    try:
        rows = connection.execute(
            "SELECT r.ext_id, s.name, r.kind, r.title, r.text FROM records r "
            "JOIN sources s ON s.id=r.source_id "
            "WHERE r.tombstoned=0 AND r.parent_id IS NULL ORDER BY r.id"
        )
        return [
            {
                "ext_id": str(row[0]),
                "source": str(row[1]),
                "kind": str(row[2]),
                "title": str(row[3] or ""),
                "text": str(row[4] or ""),
            }
            for row in rows
        ]
    finally:
        connection.close()


def stratified_sample(records: list[dict[str, str]], n: int, *, seed: int) -> list[dict[str, str]]:
    if n < 1:
        raise ValueError("n must be positive")
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for record in records:
        groups.setdefault((record["source"], record["kind"]), []).append(record)
    rng = random.Random(seed)  # noqa: S311 - seeded sampling, not cryptography
    for bucket in groups.values():
        rng.shuffle(bucket)
    keys = sorted(groups)
    picked: list[dict[str, str]] = []
    index = 0
    while len(picked) < min(n, len(records)) and keys:
        key = keys[index % len(keys)]
        bucket = groups[key]
        if bucket:
            picked.append(bucket.pop())
        if not bucket:
            keys = [item for item in keys if item != key]
            if not keys:
                break
            index = 0
            continue
        index += 1
    return picked


def _category(raw: object) -> Category:
    text = str(raw or "")
    if text in CATEGORIES:
        return text  # type: ignore[return-value]
    return "paraphrase"


def _parse_questions(text: str) -> list[dict[str, str]]:
    try:
        payload = parse_json(text)
    except ValueError:
        return []
    if isinstance(payload, dict) and "questions" in payload:
        payload = payload["questions"]
    if not isinstance(payload, list):
        return []
    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        if not question:
            continue
        rows.append({"question": question, "category": _category(item.get("category"))})
    return rows


def _ask_record(record: dict[str, str], chat: Chat) -> list[dict[str, str]]:
    prompt = PROMPT.format(
        source=record["source"],
        kind=record["kind"],
        title=record["title"],
        text=record["text"][:8000],
    )
    result = chat.complete([{"role": "user", "content": prompt}], json_mode=True, op="questions")
    parsed = _parse_questions(result.text)
    if parsed:
        low, high = QUESTIONS_PER_RECORD
        return parsed[:high] if len(parsed) >= low else parsed
    title = record["title"] or record["ext_id"]
    return [{"question": f"What does {title} cover?", "category": "paraphrase"}]


def generate_questions(
    records: list[dict[str, str]],
    *,
    n: int,
    chat: Chat | None = None,
    leakage_max: float = DEFAULT_LEAKAGE_MAX,
    seed: int = 42,
) -> GeneratedQuestions:
    if not 0 <= leakage_max <= 1:
        raise ValueError("leakage_max must be in [0, 1]")
    sampled = stratified_sample(records, n, seed=seed)
    provider: Chat = chat if chat is not None else FakeLLM()
    rows: list[EvalRow] = []
    stats = LeakageStats()
    for index, record in enumerate(sampled):
        produced = _ask_record(record, provider)
        for offset, item in enumerate(produced):
            score = leakage_score(item["question"], record["text"])
            stats.scores.append(score)
            if score > leakage_max:
                stats.dropped += 1
                continue
            stats.kept += 1
            rows.append(
                EvalRow(
                    qid=f"gen-{index:04d}-{offset}",
                    question=item["question"],
                    gold_ids=[record["ext_id"]],
                    category=_category(item["category"]),
                    source_hint=record["ext_id"],
                )
            )
    stats.histogram = leakage_histogram(stats.scores)
    return GeneratedQuestions(rows=rows, leakage=stats)


def generate_from_config(
    config: Config,
    *,
    n: int,
    chat: Chat | None = None,
    leakage_max: float = DEFAULT_LEAKAGE_MAX,
    seed: int = 42,
) -> GeneratedQuestions:
    records = load_parent_records(config)
    if not records:
        raise ValueError("workspace has no parent records to sample")
    return generate_questions(records, n=n, chat=chat, leakage_max=leakage_max, seed=seed)


def dump_evalset(rows: list[EvalRow]) -> str:
    return "\n".join(
        json.dumps(row.dump(), ensure_ascii=True, separators=(",", ":")) for row in rows
    ) + ("\n" if rows else "")


def dump_leakage(stats: LeakageStats) -> dict[str, Any]:
    return stats.dump()
