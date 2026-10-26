# SPDX-License-Identifier: Apache-2.0
"""Built-in bench strategies."""

from __future__ import annotations

from pathlib import Path

from lodestone.bench.strategies.agentic import AgenticAsk
from lodestone.bench.strategies.base import (
    ALL_STRATEGIES,
    DEFAULT_CONTEXT_BUDGET,
    IMPLEMENTED,
    IN_SCOPE,
    SKIPPED_REASONS,
    IndexStats,
    SkippedStrategy,
    Strategy,
)
from lodestone.bench.strategies.chunks import bm25_chunks, classic_rag, hybrid_chunks
from lodestone.bench.strategies.full_context import FullContext
from lodestone.bench.strategies.grep_agent import GrepAgent
from lodestone.bench.strategies.lodestone import (
    LodestoneLexical,
    lodestone_hybrid,
    lodestone_lexical,
    lodestone_rerank,
)
from lodestone.providers import Chat


def build_strategy(
    name: str,
    work: Path,
    *,
    context_budget: int = DEFAULT_CONTEXT_BUDGET,
    chat: Chat | None = None,
) -> Strategy:
    if name == "classic-rag":
        return classic_rag(work / "strategy_classic-rag.db")
    if name == "bm25-chunks":
        return bm25_chunks(work / "strategy_bm25-chunks.db")
    if name == "hybrid-chunks":
        return hybrid_chunks(work / "strategy_hybrid-chunks.db")
    if name == "lodestone-lexical":
        return lodestone_lexical(work / "strategy_lodestone-lexical", chat=chat)
    if name == "lodestone-hybrid":
        return lodestone_hybrid(work / "strategy_lodestone-hybrid", chat=chat)
    if name == "lodestone-rerank":
        return lodestone_rerank(work / "strategy_lodestone-rerank", chat=chat)
    if name == "agentic-ask":
        return AgenticAsk(work / "strategy_agentic-ask", chat=chat)
    if name == "grep-agent":
        return GrepAgent(work / "strategy_grep-agent", chat=chat)
    if name == "full-context":
        return FullContext(work / "strategy_full-context", budget=context_budget, chat=chat)
    if name in SKIPPED_REASONS:
        return SkippedStrategy(name, SKIPPED_REASONS[name])
    raise ValueError(f"unknown strategy: {name}")


def parse_names(raw: str) -> list[str]:
    if raw.strip() in {"", "all"}:
        return list(ALL_STRATEGIES)
    names = [part.strip() for part in raw.split(",") if part.strip()]
    unknown = [name for name in names if name not in ALL_STRATEGIES]
    if unknown:
        raise ValueError(f"unknown strategy: {unknown[0]}")
    return names


__all__ = [
    "ALL_STRATEGIES",
    "DEFAULT_CONTEXT_BUDGET",
    "IMPLEMENTED",
    "IN_SCOPE",
    "IndexStats",
    "LodestoneLexical",
    "SkippedStrategy",
    "Strategy",
    "build_strategy",
    "parse_names",
]
