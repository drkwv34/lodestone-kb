# SPDX-License-Identifier: Apache-2.0
"""Write card, chunk and burst embeddings in the derived-data transaction."""

from __future__ import annotations

import sqlite3

from lodestone.distill.render import embedding_input
from lodestone.storage.embeddings import write_embedding
from lodestone.vectors.embedder import Embedder

CARD_KINDS = {"doc", "code_file", "thread"}
CHUNK_KINDS = {"section", "code"}


def embed_texts(
    kind: str, text: str, norm_text: str, context_prefix: str, source: str
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if kind in CARD_KINDS:
        pieces = embedding_input(text, norm_text, source)
        joined = "\n".join(piece for piece in pieces if piece)
        if joined:
            items.append(("card", joined))
    if kind in CHUNK_KINDS:
        body = f"{context_prefix}\n{text}" if context_prefix else text
        if body:
            items.append(("chunk", body))
    if kind == "burst":
        body = f"{context_prefix}\n{text}" if context_prefix else text
        if body:
            items.append(("burst", body))
    return items


def apply_embeddings(
    connection: sqlite3.Connection,
    embedder: Embedder | None,
    source: str,
    *,
    parent_id: int | None = None,
    refresh: bool = False,
    batch_size: int = 64,
) -> int:
    if embedder is None:
        return 0
    sql = "SELECT id,kind,text,norm_text,context_prefix FROM records WHERE tombstoned=0"
    if parent_id is not None:
        sql += " AND (id=? OR parent_id=?)"
    parameters: tuple[object, ...] = (parent_id, parent_id) if parent_id is not None else ()
    pending: list[tuple[int, str, str]] = []
    for record_id, kind, text, norm_text, prefix in connection.execute(sql, parameters):
        for embed_kind, payload in embed_texts(
            str(kind), str(text), str(norm_text or ""), str(prefix or ""), source
        ):
            if not refresh:
                existing = connection.execute(
                    "SELECT dim FROM embeddings WHERE record_id=? AND kind=? AND model=?",
                    (record_id, embed_kind, embedder.model),
                ).fetchone()
                if existing and int(existing[0]) == embedder.dim:
                    continue
            pending.append((int(record_id), embed_kind, payload))
    written = 0
    for start in range(0, len(pending), batch_size):
        chunk = pending[start : start + batch_size]
        vectors = embedder.embed([item[2] for item in chunk])
        for (record_id, embed_kind, _payload), vector in zip(chunk, vectors, strict=True):
            write_embedding(connection, record_id, embed_kind, embedder.model, len(vector), vector)
            written += 1
    return written


def reindex_vectors(
    connection: sqlite3.Connection,
    embedder: Embedder | None,
    source: str,
    *,
    batch_size: int = 64,
) -> int:
    connection.execute("DELETE FROM embeddings")
    return apply_embeddings(connection, embedder, source, refresh=True, batch_size=batch_size)
