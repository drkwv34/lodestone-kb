# SPDX-License-Identifier: Apache-2.0
"""Windowed chunk strategies: classic-rag, bm25-chunks, hybrid-chunks."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from lodestone.bench.metrics import collapse_parents
from lodestone.bench.strategies.base import IndexStats
from lodestone.chunking.window import chunk as window_chunk
from lodestone.config import Source
from lodestone.connectors.files import FilesConnector, RawItem
from lodestone.connectors.threads import ThreadsConnector
from lodestone.fusion.rrf import rrf
from lodestone.lanes.fts import sanitise
from lodestone.storage.embeddings import pack_vector
from lodestone.tokenize import TOKENIZER, tokenize
from lodestone.vectors.backends import BruteForceBackend
from lodestone.vectors.hash import HashEmbedder

POOL = 80


def load_corpus(corpus: Path) -> list[RawItem]:
    items = list(
        FilesConnector().discover(
            Source(name="docs", kind="files", path=corpus, include=["docs/**", "code/**"])
        )
    )
    threads = corpus / "threads.jsonl"
    if threads.is_file():
        items.extend(
            ThreadsConnector().discover(Source(name="threads", kind="threads", path=threads))
        )
    return items


class WindowIndex:
    def __init__(self, path: Path, *, dense: bool, lexical: bool) -> None:
        self.path = path
        self.dense = dense
        self.lexical = lexical
        self.connection = sqlite3.connect(path)
        self.parent_of: dict[int, str] = {}
        self.embedder = HashEmbedder() if dense else None
        self.backend = BruteForceBackend() if dense else None
        self._prepare()

    def _prepare(self) -> None:
        self.connection.execute(
            "CREATE TABLE chunks("
            "id INTEGER PRIMARY KEY, ext_id TEXT, parent_ext_id TEXT, text TEXT)"
        )
        if self.lexical:
            self.connection.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5("
                f'parent_ext_id UNINDEXED, text, tokenize="{TOKENIZER}")'
            )
        if self.dense:
            self.connection.execute(
                "CREATE TABLE embeddings(chunk_id INTEGER PRIMARY KEY, vec BLOB)"
            )

    def add(self, parent_ext_id: str, text: str) -> int:
        tokens = 0
        for index, window in enumerate(window_chunk(text)):
            ext_id = f"{parent_ext_id}#w{index}"
            cursor = self.connection.execute(
                "INSERT INTO chunks(ext_id, parent_ext_id, text) VALUES (?,?,?)",
                (ext_id, parent_ext_id, window.text),
            )
            chunk_id = int(cursor.lastrowid or 0)
            self.parent_of[chunk_id] = parent_ext_id
            tokens += len(tokenize(window.text))
            if self.lexical:
                self.connection.execute(
                    "INSERT INTO chunks_fts(rowid, parent_ext_id, text) VALUES (?,?,?)",
                    (chunk_id, parent_ext_id, window.text),
                )
            if self.dense and self.embedder is not None:
                vector = self.embedder.embed([window.text])[0]
                self.connection.execute(
                    "INSERT INTO embeddings(chunk_id, vec) VALUES (?,?)",
                    (chunk_id, pack_vector(vector)),
                )
        return tokens

    def bm25(self, question: str, limit: int) -> list[int]:
        expression = sanitise(question, "text")
        if not expression:
            return []
        rows = self.connection.execute(
            "SELECT rowid, bm25(chunks_fts) FROM chunks_fts WHERE chunks_fts MATCH ? "
            "ORDER BY bm25(chunks_fts), rowid LIMIT ?",
            (expression, limit),
        )
        return [int(row[0]) for row in rows]

    def dense_rank(self, question: str, limit: int) -> list[int]:
        if self.embedder is None or self.backend is None:
            return []
        rows = list(
            self.connection.execute("SELECT chunk_id, vec FROM embeddings ORDER BY chunk_id")
        )
        query = self.embedder.embed([question])[0]
        return [match.record_id for match in self.backend.query(rows, query, limit)]

    def close(self) -> None:
        self.connection.close()


class ChunkStrategy:
    skipped: str | None = None

    def __init__(self, name: str, path: Path, *, dense: bool, lexical: bool) -> None:
        self.name = name
        self.path = path
        self.dense = dense
        self.lexical = lexical
        self.index_store: WindowIndex | None = None

    def index(self, corpus: Path) -> IndexStats:
        started = time.perf_counter()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.path.unlink()
        store = WindowIndex(self.path, dense=self.dense, lexical=self.lexical)
        tokens = 0
        with store.connection:
            for item in load_corpus(corpus):
                tokens += store.add(item.ext_id, item.text)
        store.connection.commit()
        self.index_store = store
        return IndexStats(
            seconds=time.perf_counter() - started,
            bytes=self.path.stat().st_size,
            in_tokens=tokens,
        )

    def retrieve(self, question: str, k: int) -> list[str]:
        store = self.index_store
        if store is None:
            raise RuntimeError(f"{self.name} must be indexed before retrieve")
        pool = max(k * 4, POOL)
        lists: dict[str, list[int]] = {}
        if self.lexical:
            lists["bm25"] = store.bm25(question, pool)
        if self.dense:
            lists["dense"] = store.dense_rank(question, pool)
        if self.dense and self.lexical:
            fused = rrf(lists, k=60)
            ranked = [ident for ident, _ in sorted(fused.items(), key=lambda item: -item[1].rrf)]
        elif self.lexical:
            ranked = lists.get("bm25", [])
        else:
            ranked = lists.get("dense", [])
        parents = collapse_parents(
            [store.parent_of[ident] for ident in ranked if ident in store.parent_of]
        )
        return parents[:k]

    def close(self) -> None:
        if self.index_store is not None:
            self.index_store.close()
            self.index_store = None


def classic_rag(path: Path) -> ChunkStrategy:
    return ChunkStrategy("classic-rag", path, dense=True, lexical=False)


def bm25_chunks(path: Path) -> ChunkStrategy:
    return ChunkStrategy("bm25-chunks", path, dense=False, lexical=True)


def hybrid_chunks(path: Path) -> ChunkStrategy:
    return ChunkStrategy("hybrid-chunks", path, dense=True, lexical=True)
