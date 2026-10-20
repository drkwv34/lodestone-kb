# SPDX-License-Identifier: Apache-2.0
"""Embedder protocol: embed(list[str]) -> list[list[float]]."""

from __future__ import annotations

from typing import Protocol

from lodestone.config import Config
from lodestone.providers.offline import OfflineError, is_offline


class Embedder(Protocol):
    model: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def make_embedder(config: Config, *, offline: bool = False) -> Embedder | None:
    """Return the configured embedder; offline always swaps to the hash embedder."""
    if offline or config.offline or is_offline():
        from lodestone.vectors.hash import HashEmbedder

        return HashEmbedder()
    if config.embed.provider == "none":
        return None
    if config.embed.provider == "hash":
        from lodestone.vectors.hash import HashEmbedder

        return HashEmbedder()
    from lodestone.vectors.openai_compat import OpenAICompatEmbedder

    return OpenAICompatEmbedder.from_config(config.embed)


__all__ = ["Embedder", "OfflineError", "make_embedder"]
