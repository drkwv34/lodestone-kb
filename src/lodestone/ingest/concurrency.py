# SPDX-License-Identifier: Apache-2.0
"""Bounded worker pool for I/O-bound LLM ingest calls."""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ConcurrencyGate:
    """Track in-flight calls and refuse to exceed `limit`."""

    def __init__(self, limit: int) -> None:
        self.limit = max(1, limit)
        self._sem = threading.BoundedSemaphore(self.limit)
        self._lock = threading.Lock()
        self._current = 0
        self.max_seen = 0

    def run(self, func: Callable[..., R], *args: object) -> R:
        with self._sem:
            with self._lock:
                self._current += 1
                self.max_seen = max(self.max_seen, self._current)
            try:
                return func(*args)
            finally:
                with self._lock:
                    self._current -= 1


def map_bounded(
    limit: int,
    func: Callable[[T], R],
    items: Sequence[T],
    *,
    gate: ConcurrencyGate | None = None,
) -> tuple[list[R], ConcurrencyGate]:
    tracker = gate or ConcurrencyGate(limit)
    if not items:
        return [], tracker
    workers = max(1, min(tracker.limit, len(items)))
    if workers == 1 or len(items) == 1:
        return [tracker.run(func, item) for item in items], tracker
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(tracker.run, func, item) for item in items]
        return [future.result() for future in futures], tracker
