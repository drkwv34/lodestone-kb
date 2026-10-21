# SPDX-License-Identifier: Apache-2.0
"""Parent collapse and per-source diversity cap for the fused candidate pool."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Ranked:
    id: int
    parent_id: int | None
    source: str
    score: float
    updated_at: str


@dataclass(frozen=True)
class Collapsed:
    id: int
    parent_id: int | None
    source: str
    score: float
    updated_at: str
    member_ids: tuple[int, ...]
    matched_children: tuple[int, ...] = field(default_factory=tuple)


def group_key(item: Ranked) -> int:
    return item.parent_id if item.parent_id is not None else item.id


def collapse(items: list[Ranked], *, max_per_source: int, pool: int) -> list[Collapsed]:
    """Keep the best-scoring member per parent, then cap sources inside the pool."""
    if max_per_source < 1 or pool < 1:
        raise ValueError("max_per_source and pool must be positive")
    grouped: dict[int, list[Ranked]] = {}
    order: list[int] = []
    for item in items:
        key = group_key(item)
        if key not in grouped:
            order.append(key)
            grouped[key] = []
        grouped[key].append(item)
    collapsed: list[Collapsed] = []
    for key in order:
        members = grouped[key]
        best = sorted(
            members, key=lambda item: (item.score, item.updated_at, -item.id), reverse=True
        )[0]
        member_ids = tuple(item.id for item in members)
        children = tuple(item.id for item in members if item.parent_id is not None)
        representative = best.parent_id if best.parent_id is not None else best.id
        collapsed.append(
            Collapsed(
                id=representative,
                parent_id=best.parent_id,
                source=best.source,
                score=best.score,
                updated_at=best.updated_at,
                member_ids=member_ids,
                matched_children=children,
            )
        )
    collapsed.sort(key=lambda item: (item.score, item.updated_at, -item.id), reverse=True)
    selected: list[Collapsed] = []
    per_source: dict[str, int] = {}
    for group in collapsed:
        taken = per_source.get(group.source, 0)
        if taken >= max_per_source:
            continue
        per_source[group.source] = taken + 1
        selected.append(group)
        if len(selected) >= pool:
            break
    return selected
