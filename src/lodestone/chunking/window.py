# SPDX-License-Identifier: Apache-2.0
"""Fixed token windows for bench baselines (512 tokens, overlap 64)."""

from __future__ import annotations

from lodestone.chunking import Chunk
from lodestone.tokenize import tokenize

WINDOW_TOKENS = 512
WINDOW_OVERLAP = 64


def _spans(text: str, tokens: list[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = 0
    folded = text.casefold()
    for token in tokens:
        needle = token.casefold()
        found = folded.find(needle, cursor)
        if found < 0:
            found = folded.find(needle)
        if found < 0:
            found = cursor
            end = cursor
        else:
            end = found + len(token)
        spans.append((found, end))
        cursor = max(cursor, end)
    return spans


def chunk(
    text: str,
    title: str = "",
    *,
    size: int = WINDOW_TOKENS,
    overlap: int = WINDOW_OVERLAP,
) -> list[Chunk]:
    """Split text into ordered token windows with a fixed overlap."""
    if size < 1:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")
    tokens = tokenize(text)
    if not tokens:
        return []
    spans = _spans(text, tokens)
    stride = size - overlap
    windows: list[Chunk] = []
    start = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        left, right = spans[start][0], spans[end - 1][1]
        piece = text[left:right] if right > left else " ".join(tokens[start:end])
        windows.append(Chunk(title=title, text=piece, start=left, end=left + len(piece)))
        if end == len(tokens):
            break
        start += stride
    return windows
