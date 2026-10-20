# SPDX-License-Identifier: Apache-2.0
"""Optional embeddings: hash and OpenAI-compatible embedders plus search backends."""

from lodestone.providers.offline import OfflineError
from lodestone.vectors.backends import BruteForceBackend, SqliteVecBackend, sqlite_vec_available
from lodestone.vectors.embedder import Embedder, make_embedder
from lodestone.vectors.hash import HASH_DIM, HASH_MODEL, HashEmbedder
from lodestone.vectors.openai_compat import OpenAICompatEmbedder

__all__ = [
    "HASH_DIM",
    "HASH_MODEL",
    "BruteForceBackend",
    "Embedder",
    "HashEmbedder",
    "OfflineError",
    "OpenAICompatEmbedder",
    "SqliteVecBackend",
    "make_embedder",
    "sqlite_vec_available",
]
