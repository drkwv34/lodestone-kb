# SPDX-License-Identifier: Apache-2.0
"""Built-in bench strategies and skipped stubs."""

from __future__ import annotations

from pathlib import Path

from lodestone.bench.strategies.base import (
    ALL_STRATEGIES,
    IN_SCOPE,
    SKIPPED_REASONS,
    IndexStats,
    SkippedStrategy,
    Strategy,
)
from lodestone.bench.strategies.chunks import bm25_chunks, classic_rag, hybrid_chunks
from lodestone.bench.strategies.lodestone import LodestoneLexical


def build_strategy(name: str, work: Path) -> Strategy:
    if name == "classic-rag":
        return classic_rag(work / "strategy_classic-rag.db")
    if name == "bm25-chunks":
        return bm25_chunks(work / "strategy_bm25-chunks.db")
    if name == "hybrid-chunks":
        return hybrid_chunks(work / "strategy_hybrid-chunks.db")
    if name == "lodestone-lexical":
        return LodestoneLexical(work / "strategy_lodestone-lexical")
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
    "IN_SCOPE",
    "IndexStats",
    "SkippedStrategy",
    "Strategy",
    "build_strategy",
    "parse_names",
]
