# SPDX-License-Identifier: Apache-2.0
"""Runtime guard that blocks remote providers while offline."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


class OfflineError(RuntimeError):
    """Raised when a remote embedder or chat provider is used while offline."""


_OFFLINE = False


def set_offline(enabled: bool) -> None:
    global _OFFLINE
    _OFFLINE = enabled


def is_offline() -> bool:
    return _OFFLINE


def reject_remote(kind: str = "provider") -> None:
    if _OFFLINE:
        raise OfflineError(f"remote {kind} is disabled while offline")


@contextmanager
def offline_scope(enabled: bool) -> Iterator[bool]:
    previous = _OFFLINE
    set_offline(enabled)
    try:
        yield enabled
    finally:
        set_offline(previous)
