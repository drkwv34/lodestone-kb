# SPDX-License-Identifier: Apache-2.0
"""Cosine vector search: brute-force (array/numpy) and optional sqlite-vec."""

from __future__ import annotations

import array
import sqlite3
import struct
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class VectorMatch:
    record_id: int
    score: float


def sqlite_vec_available() -> bool:
    try:
        import sqlite_vec  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        return False
    return True


def load_sqlite_vec(connection: sqlite3.Connection) -> bool:
    try:
        import sqlite_vec

        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        return True
    except (ImportError, sqlite3.Error, AttributeError, OSError):
        return False


def _numpy_scores(
    query: list[float], rows: list[tuple[int, bytes]]
) -> list[tuple[int, float]] | None:
    try:
        import numpy as np
    except ImportError:
        return None
    dim = len(query)
    matrix = np.frombuffer(b"".join(blob for _, blob in rows), dtype="<f4")
    if matrix.size != len(rows) * dim:
        return None
    scores = matrix.reshape(len(rows), dim) @ np.asarray(query, dtype=np.float32)
    return [(rows[index][0], float(scores[index])) for index in range(len(rows))]


def _dot_scores(
    query: list[float], rows: list[tuple[int, bytes]], *, use_numpy: bool
) -> list[tuple[int, float]]:
    if use_numpy:
        packed = _numpy_scores(query, rows)
        if packed is not None:
            return packed
    scored: list[tuple[int, float]] = []
    for record_id, blob in rows:
        vector = array.array("f")
        vector.frombytes(blob)
        if sys.byteorder != "little":
            vector.byteswap()
        if len(vector) != len(query):
            continue
        scored.append((record_id, sum(a * b for a, b in zip(query, vector, strict=True))))
    return scored


class BruteForceBackend:
    """Exact cosine via L2-normalised dot product; numpy is used when installed."""

    def __init__(self, *, use_numpy: bool | None = None) -> None:
        if use_numpy is None:
            try:
                import numpy as np  # noqa: F401
            except ImportError:
                use_numpy = False
            else:
                use_numpy = True
        self.use_numpy = use_numpy

    def query(
        self, rows: list[tuple[int, bytes]], query: list[float], limit: int
    ) -> list[VectorMatch]:
        if not rows or limit < 1:
            return []
        scored = _dot_scores(query, rows, use_numpy=self.use_numpy)
        scored.sort(key=lambda item: (-item[1], item[0]))
        return [VectorMatch(record_id, score) for record_id, score in scored[:limit]]


class SqliteVecBackend:
    """Lazily built per (model, dim) sqlite-vec index over embedding BLOBs."""

    def query(
        self,
        rows: list[tuple[int, bytes]],
        query: list[float],
        limit: int,
        *,
        model: str,
        dim: int,
    ) -> list[VectorMatch]:
        if not rows or limit < 1:
            return []
        if not model:
            return BruteForceBackend().query(rows, query, limit)
        connection = sqlite3.connect(":memory:")
        try:
            if not load_sqlite_vec(connection):
                return BruteForceBackend().query(rows, query, limit)
            ddl = (
                "CREATE VIRTUAL TABLE vec_index USING vec0(embedding float["
                + str(int(dim))
                + "] distance_metric=cosine)"
            )
            connection.execute(ddl)
            for record_id, blob in rows:
                connection.execute(
                    "INSERT INTO vec_index(rowid, embedding) VALUES (?, ?)",
                    (record_id, blob),
                )
            packed = struct.pack("<" + "f" * dim, *[float(item) for item in query])
            matches = connection.execute(
                "SELECT rowid, distance FROM vec_index WHERE embedding MATCH ? AND k = ? "
                "ORDER BY distance",
                (packed, limit),
            ).fetchall()
            return [
                VectorMatch(int(record_id), 1.0 - float(distance))
                for record_id, distance in matches
            ]
        except sqlite3.Error:
            return BruteForceBackend().query(rows, query, limit)
        finally:
            connection.close()
