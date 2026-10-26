# SPDX-License-Identifier: Apache-2.0
"""Versioned structural ingestion, atomic parent replacement and incremental deletion."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import chain

from lodestone.chunking import code, markdown
from lodestone.config import Chunks, Config, Source
from lodestone.connectors.files import CODE_KINDS, RawItem
from lodestone.connectors.plugins import connector_for
from lodestone.distill.apply import (
    CardStats,
    CardWork,
    bind_log,
    commit_generated_card,
    contextualize_children,
    flush_cost_log,
    generate_card,
    pending_card_work,
    requeue_embeddings,
)
from lodestone.distill.schema import Card
from lodestone.ingest.concurrency import map_bounded
from lodestone.ingest.crash import maybe_crash
from lodestone.ingest.embeddings import apply_embeddings
from lodestone.ingest.hashing import CHUNKER_VERSION, content_hash
from lodestone.ingest.thread_sync import ingest_thread_lexical, refresh_burst_prefixes
from lodestone.observe import timed
from lodestone.providers import Chat
from lodestone.providers.chat import ChatResult
from lodestone.storage.costs import log_call
from lodestone.storage.registry import reconcile, register
from lodestone.vectors.embedder import Embedder
from lodestone.vectors.openai_compat import OpenAICompatEmbedder

__all__ = ["CHUNKER_VERSION", "SyncReport", "content_hash", "sync", "upsert"]


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
    max_concurrency: int = 0


def upsert(
    connection: sqlite3.Connection, source_id: int, item: RawItem, chunks: Chunks | None = None
) -> tuple[bool, int]:
    cfg = chunks or Chunks()
    version = CHUNKER_VERSION + ":" + item.kind_hint + ":" + cfg.model_dump_json()
    digest = content_hash(item.text, version)
    existing = connection.execute(
        "SELECT id,content_hash,tombstoned,derived_state FROM records "
        "WHERE source_id=? AND ext_id=?",
        (source_id, item.ext_id),
    ).fetchone()
    if existing and existing[1] == digest and not existing[2]:
        return False, int(existing[0])
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
    return True, int(parent_id)


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


def _needs_derived(connection: sqlite3.Connection, parent_id: int) -> bool:
    row = connection.execute(
        "SELECT derived_state FROM records WHERE id=?", (parent_id,)
    ).fetchone()
    return row is None or str(row[0]) != "ok"


def _finish_derived(
    connection: sqlite3.Connection,
    parent_ids: list[int],
    config: Config,
    chat: Chat | None,
    stats: CardStats,
    *,
    refresh_cards: bool,
    embedder: Embedder | None,
) -> int:
    jobs: list[CardWork] = []
    with connection:
        for parent_id in parent_ids:
            jobs.extend(
                pending_card_work(connection, parent_id, config, chat, stats, refresh=refresh_cards)
            )
    limit = config.llm.max_concurrency if config.llm is not None else 4

    def generate(work: CardWork) -> tuple[CardWork, Card, str]:
        card, used = generate_card(
            work.title, work.text, work.kind, config, chat, None, messages=work.messages
        )
        return work, card, used

    produced, gate = (
        map_bounded(limit, generate, jobs)
        if jobs and chat is not None
        else (
            [
                (
                    work,
                    *generate_card(
                        work.title,
                        work.text,
                        work.kind,
                        config,
                        chat,
                        connection,
                        messages=work.messages,
                    ),
                )
                for work in jobs
            ],
            None,
        )
    )
    pending = [
        parent_id
        for parent_id in parent_ids
        if refresh_cards or _needs_derived(connection, parent_id)
    ]
    if not jobs and not pending:
        return 0
    with connection:
        flush_cost_log(connection, stats)
        for work, card, used in produced:
            commit_generated_card(connection, work, card, used, config, stats)
        targets = pending or parent_ids
        for parent_id in targets:
            contextualize_children(connection, parent_id, config, chat)
            title_row = connection.execute(
                "SELECT title FROM records WHERE id=?", (parent_id,)
            ).fetchone()
            refresh_burst_prefixes(connection, parent_id, str(title_row[0]) if title_row else "")
            apply_embeddings(
                connection,
                embedder,
                config.embed.source,
                parent_id=parent_id,
                batch_size=config.embed.batch_size,
            )
            connection.execute(
                "UPDATE records SET derived_state='ok' WHERE id=? AND derived_state='pending'",
                (parent_id,),
            )
        flush_cost_log(connection, stats)
    return gate.max_seen if gate is not None else (1 if jobs else 0)


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
    with timed("sync"):
        for source in selected:
            _sync_source(
                connection,
                config,
                source,
                chat=chat,
                refresh_cards=refresh_cards,
                embedder=embedder,
                stats=stats,
                prune=prune,
                report=report,
            )
        with connection:
            flush_cost_log(connection, stats)
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


def _sync_source(
    connection: sqlite3.Connection,
    config: Config,
    source: Source,
    *,
    chat: Chat | None,
    refresh_cards: bool,
    embedder: Embedder | None,
    stats: CardStats,
    prune: bool,
    report: SyncReport,
) -> None:
    connector = connector_for(source)
    items = connector.discover(source)
    first = next(items, None)
    with connection:
        source_id = register(connection, source)
    changed = False
    seen: set[str] = set()
    derived: list[int] = []
    for item in chain([first] if first is not None else [], items):
        seen.add(item.ext_id)
        if source.kind == "threads":
            wrote, parent_id = ingest_thread_lexical(connection, source_id, item, config)
        else:
            wrote, parent_id = upsert(connection, source_id, item, config.chunks)
        maybe_crash()
        derived.append(parent_id)
        if wrote:
            report.processed += 1
            changed = True
        else:
            report.unchanged += 1
    skipped = getattr(connector, "skipped", [])
    report.skipped += len(skipped)
    if derived:
        seen_max = _finish_derived(
            connection,
            derived,
            config,
            chat,
            stats,
            refresh_cards=refresh_cards,
            embedder=embedder,
        )
        report.max_concurrency = max(report.max_concurrency, seen_max)
    before = report.tombstoned + report.pruned
    remove_missing(
        connection,
        source_id,
        seen,
        [skip.path for skip in skipped if not skip.path.startswith("line ")],
        prune=prune,
        report=report,
    )
    if changed or before != report.tombstoned + report.pruned:
        with connection:
            connection.execute(
                "UPDATE sources SET last_synced_at=? WHERE id=?",
                (datetime.now(UTC).isoformat(), source_id),
            )
