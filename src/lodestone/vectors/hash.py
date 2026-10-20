# SPDX-License-Identifier: Apache-2.0
"""Deterministic 256-d hash embedder. Not semantic: tests and offline demos only."""

from __future__ import annotations

import hashlib
import itertools
import math

from lodestone.tokenize import tokenize

HASH_DIM = 256
HASH_MODEL = "hash"


def _feature_hash(feature: str) -> tuple[int, float]:
    digest = hashlib.sha256(feature.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "little", signed=False)
    index = (value >> 1) % HASH_DIM
    sign = 1.0 if (value & 1) == 0 else -1.0
    return index, sign


def _normalise(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0.0:
        return vector
    return [item / norm for item in vector]


def hash_vector(text: str) -> list[float]:
    """Signed feature hashing of tokens and adjacent bigrams, then L2-normalise."""
    tokens = tokenize(text)
    vector = [0.0] * HASH_DIM
    features = list(tokens)
    features.extend(f"{left}\x00{right}" for left, right in itertools.pairwise(tokens))
    for feature in features:
        index, sign = _feature_hash(feature)
        vector[index] += sign
    return _normalise(vector)


class HashEmbedder:
    """256-dimensional signed-hash embedder. Deterministic and not semantic."""

    model: str = HASH_MODEL
    dim: int = HASH_DIM

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [hash_vector(text) for text in texts]
