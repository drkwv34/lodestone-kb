# SPDX-License-Identifier: Apache-2.0
"""Pack and persist embedding BLOBs; storage owns the embeddings table."""

from __future__ import annotations

import sqlite3
import struct


def pack_vector(values: list[float]) -> bytes:
    return struct.pack("<" + "f" * len(values), *[float(item) for item in values])


def unpack_vector(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack("<" + "f" * count, blob))


def write_embedding(
    connection: sqlite3.Connection,
    record_id: int,
    kind: str,
    model: str,
    dim: int,
    vector: list[float],
) -> None:
    connection.execute(
        "INSERT INTO embeddings(record_id, kind, model, dim, vec) VALUES(?,?,?,?,?) "
        "ON CONFLICT(record_id, kind, model) DO UPDATE SET dim=excluded.dim, vec=excluded.vec",
        (record_id, kind, model, dim, pack_vector(vector)),
    )


def delete_for_record(connection: sqlite3.Connection, record_id: int) -> None:
    connection.execute("DELETE FROM embeddings WHERE record_id=?", (record_id,))


def matching_count(
    connection: sqlite3.Connection, model: str, dim: int, kinds: tuple[str, ...]
) -> int:
    total = 0
    for kind in kinds:
        row = connection.execute(
            "SELECT count(*) FROM embeddings e JOIN records r ON r.id=e.record_id "
            "WHERE e.model=? AND e.dim=? AND r.tombstoned=0 AND e.kind=?",
            (model, dim, kind),
        ).fetchone()
        total += int(row[0]) if row else 0
    return total
