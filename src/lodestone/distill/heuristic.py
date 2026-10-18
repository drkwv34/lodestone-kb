# SPDX-License-Identifier: Apache-2.0
"""Network-free heuristic cards used as fallback and offline distillation."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable
from functools import partial

from lodestone.distill.render import clip, with_provenance
from lodestone.distill.schema import Card
from lodestone.storage.terms import idf as term_idf
from lodestone.tokenize import tokenize

SENTENCES = re.compile(r"(?<=[.!?])\s+")
CANDIDATE = re.compile(
    r"\b(?:[A-Z][a-zA-Z0-9_-]*|[A-Za-z]+[0-9][A-Za-z0-9_-]*|[a-z]+(?:[A-Z][a-zA-Z0-9]*)+|"
    r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+)\b"
)
CODE_PATTERNS = (
    re.compile(r"\b[A-Z][A-Z0-9_]{3,}\b"),
    re.compile(r"\b[a-z][a-z0-9]*(_[a-z0-9]+)+\b"),
    re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+\b"),
    re.compile(r"\b(?:[\w.-]+/)+\w+\.\w+\b"),
    re.compile(r"\b(?:E\d{2,}|ERR_[A-Z0-9_]+)\b"),
)


def sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCES.split(text.replace("\r\n", "\n")) if part.strip()]


def first_line(text: str) -> str:
    line = text.split("\n", 1)[0].strip()
    return re.sub(r"^#+\s*", "", line)


def question_of(title: str, text: str) -> str:
    if title.strip():
        return clip(title.strip(), 200)
    for sentence in sentences(text):
        if sentence.endswith("?"):
            return clip(sentence, 200)
    return clip(first_line(text) or "unknown", 200)


def summary_of(text: str) -> str:
    return clip(" ".join(sentences(text)[:2]) or first_line(text), 300)


def code_refs_of(text: str, limit: int = 12) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for pattern in CODE_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            if value not in seen:
                seen.add(value)
                found.append(value)
            if len(found) >= limit:
                return found
    return found


def entities_of(
    text: str, score: Callable[[str], float], limit: int = 5, banned: set[str] | None = None
) -> list[str]:
    skip = banned or set()
    found: list[str] = []
    seen: set[str] = set()
    for match in CANDIDATE.finditer(text):
        raw = match.group(0)
        tokens = tokenize(raw)
        key = tokens[0] if tokens else raw.lower()
        if key in seen or key in skip or len(raw) < 2:
            continue
        seen.add(key)
        found.append(raw)
    return sorted(found, key=lambda term: -score(_token(term)))[:limit]


def _token(term: str) -> str:
    tokens = tokenize(term)
    return tokens[0] if tokens else term.lower()


def _idf(connection: sqlite3.Connection | None, term: str) -> float:
    return 0.0 if connection is None else term_idf(connection, term)


def heuristic_card(
    title: str,
    text: str,
    *,
    messages: list[tuple[str, str]] | None = None,
    connection: sqlite3.Connection | None = None,
    kind: str = "doc",
) -> Card:
    del kind
    refs = code_refs_of(text)
    banned = {_token(item) for item in refs}
    resolution = clip(messages[-1][1], 500) if messages else ""
    card = Card(
        question=question_of(title, text),
        summary=summary_of(text),
        resolution=resolution,
        entities=entities_of(text, partial(_idf, connection), banned=banned),
        code_refs=refs,
    )
    return with_provenance(card, text, [item[0] for item in messages] if messages else None)
