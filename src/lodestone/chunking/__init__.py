# SPDX-License-Identifier: Apache-2.0
"""Structural chunks retain exact character spans in the original source."""

from dataclasses import dataclass
from itertools import pairwise

from lodestone.config import Chunks


@dataclass(frozen=True)
class Chunk:
    title: str
    text: str
    start: int
    end: int


def pack(text: str, boundaries: list[int], config: Chunks) -> list[tuple[int, int]]:
    """Pack indivisible units near the target; split oversized units at line/space boundaries."""
    target = config.target_tokens * config.chars_per_token
    maximum = config.max_tokens * config.chars_per_token
    result: list[tuple[int, int]] = []
    start = end = boundaries[0]
    for left, right in pairwise(boundaries):
        if end > start and (end - start >= target or right - start > maximum):
            result.append((start, end))
            start = left
        while right - left > maximum:
            if end > start:
                result.append((start, end))
            limit = left + maximum
            split = text.rfind("\n", left, limit) + 1
            if split <= left:
                split = text.rfind(" ", left, limit) + 1
            if split <= left:
                split = limit
            result.append((left, split))
            left = split
            start = end = left
        end = right
    if end > start:
        result.append((start, end))
    return result
