# SPDX-License-Identifier: Apache-2.0
"""Strategy protocol, index stats, and catalog of built-in names."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class IndexStats:
    seconds: float
    bytes: int
    in_tokens: int = 0
    out_tokens: int = 0


class Strategy(Protocol):
    name: str
    skipped: str | None

    def index(self, corpus: Path) -> IndexStats: ...

    def retrieve(self, question: str, k: int) -> list[str]: ...

    def close(self) -> None: ...


class SkippedStrategy:
    """Placeholder for strategies that are not implemented."""

    name: str
    skipped: str | None

    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.skipped = reason

    def index(self, corpus: Path) -> IndexStats:
        return IndexStats(seconds=0.0, bytes=0)

    def retrieve(self, question: str, k: int) -> list[str]:
        return []

    def close(self) -> None:
        return None


SKIPPED_REASONS: dict[str, str] = {}
IN_SCOPE = ("classic-rag", "bm25-chunks", "hybrid-chunks", "lodestone-lexical")
IMPLEMENTED = (
    *IN_SCOPE,
    "lodestone-hybrid",
    "lodestone-rerank",
    "agentic-ask",
    "grep-agent",
    "full-context",
)
ALL_STRATEGIES = IMPLEMENTED
DEFAULT_CONTEXT_BUDGET = 128_000
