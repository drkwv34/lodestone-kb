# SPDX-License-Identifier: Apache-2.0
"""Versioned structural ingestion, atomic parent replacement and incremental deletion."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import chain

from lodestone.chunking import code, markdown
from lodestone.config import Chunks, Config, Source
from lodestone.connectors.files import CODE_KINDS, FilesConnector, RawItem
from lodestone.connectors.threads import ThreadsConnector
from lodestone.distill.apply import (
    CardStats,
    apply_cards,
    bind_log,
    contextualize_children,
    requeue_embeddings,
)
from lodestone.ingest.bursts import qualifying_bursts
from lodestone.ingest.embeddings import apply_embeddings
from lodestone.providers import Chat
from lodestone.providers.chat import ChatResult
from lodestone.storage.costs import log_call
from lodestone.storage.registry import reconcile, register
from lodestone.storage.terms import idf as term_idf
from lodestone.vectors.embedder import Embedder
from lodestone.vectors.openai_compat import OpenAICompatEmbedder

CHUNKER_VERSION = markdown.VERSION + "/" + code.VERSION
THREAD_VERSION = "thread-v1"


def content_hash(text: str, version: str = CHUNKER_VERSION) -> str:
    normalised = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return hashlib.sha256((version + "\x00" + normalised).encode("utf-8")).hexdigest()


@dataclass
class SyncReport:
    processed: int = 0
    unchanged: int = 0
    skipped: int = 0
    llm_calls: int = 0
    tombstoned: int = 0
    pruned: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cards_llm: int = 0
    cards_heuristic: int = 0


def connector_for(source: Source) -> FilesConnector | ThreadsConnector:
    if source.kind == "files":
        return FilesConnector()
    if source.kind == "threads":
        return ThreadsConnector()
    raise ValueError(f"unsupported source kind: {source.kind}")


def upsert(
    connection: sqlite3.Connection, source_id: int, item: RawItem, chunks: Chunks | None = None
) -> bool:
    cfg = chunks or Chunks()
    version = CHUNKER_VERSION + ":" + item.kind_hint + ":" + cfg.model_dump_json()
    digest = content_hash(item.text, version)
    existing = connection.execute(
        "SELECT id,content_hash,tombstoned FROM records WHERE source_id=? AND ext_id=?",
        (source_id, item.ext_id),
    ).fetchone()
    if existing and existing[1] == digest and not existing[2]:
        return False
    is_code = item.kind_hint in CODE_KINDS
    outline = code.outline(item.text, item.kind_hint) if is_code else ""
    children = (
        code.chunk(item.text, item.kind_hint, item.title, cfg)
        if is_code
        else markdown.chunk(item.text, item.title, cfg)
    )
    now = datetime.now(UTC).isoformat()
    updated = item.updated_at.isoformat()
    with connection:
        connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,title,text,context_prefix,metadata_json,"
            "content_hash,created_at,updated_at,indexed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(source_id,ext_id) DO UPDATE SET kind=excluded.kind,"
            "title=excluded.title,text=excluded.text,context_prefix=excluded.context_prefix,"
            "metadata_json=excluded.metadata_json,content_hash=excluded.content_hash,"
            "updated_at=excluded.updated_at,indexed_at=excluded.indexed_at,derived_state='pending',"
            "tombstoned=0,card_json=NULL,card_method=NULL,norm_text=''",
            (
                source_id,
                item.ext_id,
                "code_file" if is_code else "doc",
                item.title,
                item.text,
                outline,
                json.dumps(item.metadata),
                digest,
                updated,
                updated,
                now,
            ),
        )
        parent_id = connection.execute(
            "SELECT id FROM records WHERE source_id=? AND ext_id=?", (source_id, item.ext_id)
        ).fetchone()[0]
        connection.execute("DELETE FROM embeddings WHERE record_id=?", (parent_id,))
        connection.execute("DELETE FROM records WHERE parent_id=?", (parent_id,))
        child_kind = "code" if is_code else "section"
        for seq, child in enumerate(children):
            metadata = {**item.metadata, "start": child.start, "end": child.end}
            connection.execute(
                "INSERT INTO records(source_id,ext_id,parent_id,kind,seq,title,text,metadata_json,"
                "content_hash,created_at,updated_at,indexed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    source_id,
                    f"{item.ext_id}#{child_kind}:{seq}",
                    parent_id,
                    child_kind,
                    seq,
                    child.title,
                    child.text,
                    json.dumps(metadata),
                    content_hash(child.text, version),
                    updated,
                    updated,
                    now,
                ),
            )
    return True


def _bind_embed_log(embedder: Embedder | None, connection: sqlite3.Connection) -> None:
    if not isinstance(embedder, OpenAICompatEmbedder):
        return
    previous = embedder.log

    def log(op: str, result: ChatResult) -> None:
        log_call(
            connection,
            op=op,
            model=result.model,
            in_tokens=result.in_tokens,
            out_tokens=result.out_tokens,
            latency_ms=result.latency_ms,
            ok=result.ok,
        )
        if callable(previous):
            previous(op, result)

    embedder.log = log


def ingest_thread(
    connection: sqlite3.Connection,
    source_id: int,
    item: RawItem,
    config: Config,
    chat: Chat | None,
    stats: CardStats,
    *,
    refresh_cards: bool,
    embedder: Embedder | None = None,
) -> bool:
    version = THREAD_VERSION + ":thread"
    digest = content_hash(item.text, version)
    existing = connection.execute(
        "SELECT id,content_hash,tombstoned FROM records WHERE source_id=? AND ext_id=?",
        (source_id, item.ext_id),
    ).fetchone()
    if existing and existing[1] == digest and not existing[2]:
        with connection:
            apply_cards(connection, int(existing[0]), config, chat, stats, refresh=refresh_cards)
            apply_embeddings(
                connection,
                embedder,
                config.embed.source,
                parent_id=int(existing[0]),
                batch_size=config.embed.batch_size,
            )
        return False
    messages = item.messages or ()
    authors = list(dict.fromkeys(message.author for message in messages))
    now = datetime.now(UTC).isoformat()
    updated = item.updated_at.isoformat()
    with connection:
        connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,title,text,author,authors_json,"
            "metadata_json,content_hash,created_at,updated_at,indexed_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(source_id,ext_id) DO UPDATE SET kind=excluded.kind,"
            "title=excluded.title,text=excluded.text,author=excluded.author,"
            "authors_json=excluded.authors_json,metadata_json=excluded.metadata_json,"
            "content_hash=excluded.content_hash,updated_at=excluded.updated_at,"
            "indexed_at=excluded.indexed_at,derived_state='pending',tombstoned=0,"
            "card_json=NULL,card_method=NULL,norm_text='',context_prefix=''",
            (
                source_id,
                item.ext_id,
                "thread",
                item.title,
                item.text,
                authors[0] if authors else None,
                json.dumps(authors),
                json.dumps(item.metadata),
                digest,
                updated,
                updated,
                now,
            ),
        )
        parent_id = int(
            connection.execute(
                "SELECT id FROM records WHERE source_id=? AND ext_id=?", (source_id, item.ext_id)
            ).fetchone()[0]
        )
        connection.execute("DELETE FROM embeddings WHERE record_id=?", (parent_id,))
        connection.execute("DELETE FROM records WHERE parent_id=?", (parent_id,))
        apply_cards(connection, parent_id, config, chat, stats, refresh=refresh_cards)
        _write_bursts(connection, source_id, parent_id, item, config, version, updated, now)
        apply_embeddings(
            connection,
            embedder,
            config.embed.source,
            parent_id=parent_id,
            batch_size=config.embed.batch_size,
        )
    return True


def _write_bursts(
    connection: sqlite3.Connection,
    source_id: int,
    parent_id: int,
    item: RawItem,
    config: Config,
    version: str,
    updated: str,
    now: str,
) -> None:
    prefix = _burst_prefix(connection, parent_id, item.title)
    kept = qualifying_bursts(
        item.messages or (), config.bursts, lambda term: term_idf(connection, term)
    )
    for seq, burst in enumerate(kept):
        metadata = {
            **item.metadata,
            "message_ids": json.dumps([message.id for message in burst.messages]),
        }
        connection.execute(
            "INSERT INTO records(source_id,ext_id,parent_id,kind,seq,title,text,context_prefix,"
            "author,authors_json,metadata_json,content_hash,created_at,updated_at,indexed_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                source_id,
                f"{item.ext_id}#burst:{burst.group}",
                parent_id,
                "burst",
                seq,
                item.title,
                burst.text,
                prefix,
                burst.author,
                json.dumps([burst.author]),
                json.dumps(metadata),
                content_hash(burst.text, version),
                updated,
                updated,
                now,
            ),
        )


def _burst_prefix(connection: sqlite3.Connection, parent_id: int, title: str) -> str:
    row = connection.execute("SELECT card_json FROM records WHERE id=?", (parent_id,)).fetchone()
    if row and row[0]:
        try:
            question = json.loads(row[0]).get("question")
        except json.JSONDecodeError:
            question = None
        if isinstance(question, str) and question.strip():
            return question.strip()
    return title


def remove_missing(
    connection: sqlite3.Connection,
    source_id: int,
    seen: set[str],
    protected: list[str],
    *,
    prune: bool,
    report: SyncReport,
) -> None:
    with connection:
        for record_id, ext_id, tombstoned in connection.execute(
            "SELECT id,ext_id,tombstoned FROM records WHERE source_id=? AND parent_id IS NULL",
            (source_id,),
        ).fetchall():
            if ext_id in seen or any(
                ext_id == path or ext_id.startswith(path.rstrip("/") + "/") for path in protected
            ):
                continue
            if not tombstoned:
                connection.execute(
                    "UPDATE records SET tombstoned=1 WHERE (id=? OR parent_id=?) AND tombstoned=0",
                    (record_id, record_id),
                )
                report.tombstoned += 1
            if prune:
                connection.execute("DELETE FROM records WHERE id=?", (record_id,))
                report.pruned += 1


def sync(
    connection: sqlite3.Connection,
    config: Config,
    *,
    sources: list[str] | None = None,
    project: str | None = None,
    prune: bool = False,
    chat: Chat | None = None,
    refresh_cards: bool = False,
    embedder: Embedder | None = None,
) -> SyncReport:
    names = config.scoped_sources(project, sources)
    selected = [source for source in config.sources if source.name in names]
    report = SyncReport()
    stats = CardStats()
    if chat is not None:
        bind_log(chat, connection, stats)
    _bind_embed_log(embedder, connection)
    with connection:
        requeue_embeddings(connection, config.embed.source)
    for source in selected:
        connector = connector_for(source)
        items = connector.discover(source)
        first = next(items, None)
        with connection:
            source_id = register(connection, source)
        changed = False
        seen: set[str] = set()
        for item in chain([first] if first is not None else [], items):
            seen.add(item.ext_id)
            if source.kind == "threads":
                wrote = ingest_thread(
                    connection,
                    source_id,
                    item,
                    config,
                    chat,
                    stats,
                    refresh_cards=refresh_cards,
                    embedder=embedder,
                )
            else:
                wrote = upsert(connection, source_id, item, config.chunks)
                parent = connection.execute(
                    "SELECT id FROM records WHERE source_id=? AND ext_id=?",
                    (source_id, item.ext_id),
                ).fetchone()
                if parent is not None:
                    with connection:
                        apply_cards(
                            connection, int(parent[0]), config, chat, stats, refresh=refresh_cards
                        )
                        contextualize_children(connection, int(parent[0]), config, chat)
                        apply_embeddings(
                            connection,
                            embedder,
                            config.embed.source,
                            parent_id=int(parent[0]),
                            batch_size=config.embed.batch_size,
                        )
            if wrote:
                report.processed += 1
                changed = True
            else:
                report.unchanged += 1
        report.skipped += len(connector.skipped)
        before = report.tombstoned + report.pruned
        remove_missing(
            connection,
            source_id,
            seen,
            [skip.path for skip in connector.skipped if not skip.path.startswith("line ")],
            prune=prune,
            report=report,
        )
        if changed or before != report.tombstoned + report.pruned:
            with connection:
                connection.execute(
                    "UPDATE sources SET last_synced_at=? WHERE id=?",
                    (datetime.now(UTC).isoformat(), source_id),
                )
    with connection:
        apply_embeddings(
            connection, embedder, config.embed.source, batch_size=config.embed.batch_size
        )
        reconcile(connection, config)
    report.llm_calls = stats.llm_calls
    report.cache_hits = stats.cache_hits
    report.cache_misses = stats.cache_misses
    report.cards_llm = stats.cards_llm
    report.cards_heuristic = stats.cards_heuristic
    return report
