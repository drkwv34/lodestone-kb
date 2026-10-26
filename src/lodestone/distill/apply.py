# SPDX-License-Identifier: Apache-2.0
"""Card cache, record writes and optional chunk contextual prefixes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime

from lodestone.config import Config
from lodestone.distill.heuristic import heuristic_card
from lodestone.distill.llm import llm_card
from lodestone.distill.render import render_norm
from lodestone.distill.schema import Card
from lodestone.providers import Chat
from lodestone.providers.chat import ChatResult
from lodestone.storage.costs import log_call


@dataclass
class CardStats:
    llm_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cards_llm: int = 0
    cards_heuristic: int = 0
    pending_calls: list[tuple[str, ChatResult]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


@dataclass(frozen=True)
class CardWork:
    record_id: int
    title: str
    text: str
    kind: str
    digest: str
    messages: list[tuple[str, str]] | None
    key: str


def cache_key(content_hash: str, prompt_version: str, model: str) -> str:
    payload = f"{content_hash}\0{prompt_version}\0{model}".encode()
    return hashlib.sha256(payload).hexdigest()


def bind_log(chat: Chat, connection: sqlite3.Connection, stats: CardStats) -> None:
    del connection
    previous = chat.log

    def log(op: str, result: ChatResult) -> None:
        with stats._lock:
            stats.pending_calls.append((op, result))
        if previous is not None:
            previous(op, result)

    chat.log = log


def flush_cost_log(connection: sqlite3.Connection, stats: CardStats) -> None:
    with stats._lock:
        pending = list(stats.pending_calls)
        stats.pending_calls.clear()
    for op, result in pending:
        log_call(
            connection,
            op=op,
            model=result.model,
            in_tokens=result.in_tokens,
            out_tokens=result.out_tokens,
            latency_ms=result.latency_ms,
            ok=result.ok,
        )
        stats.llm_calls += 1


def pending_card_work(
    connection: sqlite3.Connection,
    parent_id: int,
    config: Config,
    chat: Chat | None,
    stats: CardStats,
    *,
    refresh: bool = False,
) -> list[CardWork]:
    if not config.cards.enabled:
        return []
    model = chat.model if chat is not None else "heuristic"
    kinds = set(config.cards.kinds)
    jobs: list[CardWork] = []
    rows = connection.execute(
        "SELECT id,kind,title,text,content_hash,card_json,card_method,norm_text,metadata_json "
        "FROM records WHERE (id=? OR parent_id=?) AND tombstoned=0",
        (parent_id, parent_id),
    ).fetchall()
    for row in rows:
        record_id, kind, title, text, digest, stored, method, norm, metadata_json = row
        if kind not in kinds:
            continue
        key = cache_key(str(digest), config.cards.prompt_version, model)
        if not refresh:
            cached = connection.execute(
                "SELECT card_json, method FROM card_cache WHERE key=?", (key,)
            ).fetchone()
            if cached:
                stats.cache_hits += 1
                card = Card.model_validate_json(cached[0])
                rendered = render_norm(card, config.cards.norm_format)
                if stored == cached[0] and method == cached[1] and norm == rendered:
                    continue
                _write(connection, int(record_id), cached[0], str(cached[1]), rendered)
                continue
        stats.cache_misses += 1
        jobs.append(
            CardWork(
                record_id=int(record_id),
                title=str(title),
                text=str(text),
                kind=str(kind),
                digest=str(digest),
                messages=_thread_messages(str(kind), str(metadata_json or "")),
                key=key,
            )
        )
    return jobs


def commit_generated_card(
    connection: sqlite3.Connection,
    work: CardWork,
    card: Card,
    used: str,
    config: Config,
    stats: CardStats,
) -> None:
    payload = card.model_dump_json()
    rendered = render_norm(card, config.cards.norm_format)
    _write(connection, work.record_id, payload, used, rendered)
    connection.execute(
        "INSERT INTO card_cache(key,card_json,method,created_at) VALUES(?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET card_json=excluded.card_json,"
        "method=excluded.method,created_at=excluded.created_at",
        (work.key, payload, used, datetime.now(UTC).isoformat()),
    )
    if used == "llm":
        stats.cards_llm += 1
    else:
        stats.cards_heuristic += 1


def apply_cards(
    connection: sqlite3.Connection,
    parent_id: int,
    config: Config,
    chat: Chat | None,
    stats: CardStats,
    *,
    refresh: bool = False,
) -> None:
    for work in pending_card_work(connection, parent_id, config, chat, stats, refresh=refresh):
        card, used = generate_card(
            work.title,
            work.text,
            work.kind,
            config,
            chat,
            connection,
            messages=work.messages,
        )
        commit_generated_card(connection, work, card, used, config, stats)


def contextualize_children(
    connection: sqlite3.Connection, parent_id: int, config: Config, chat: Chat | None
) -> None:
    if not config.chunks.contextualize:
        return
    parent = connection.execute("SELECT title FROM records WHERE id=?", (parent_id,)).fetchone()
    title = str(parent[0]) if parent else ""
    children = connection.execute(
        "SELECT id,kind,title,text,norm_text FROM records WHERE parent_id=? AND kind IN "
        "('section','code') AND tombstoned=0",
        (parent_id,),
    ).fetchall()
    for record_id, kind, child_title, text, norm in children:
        prefix = _prefix(str(kind), str(child_title) or title, str(text), chat)
        connection.execute("UPDATE records SET context_prefix=? WHERE id=?", (prefix, record_id))
        if not str(norm):
            connection.execute("UPDATE records SET norm_text=? WHERE id=?", (prefix, record_id))


def requeue_embeddings(connection: sqlite3.Connection, source: str) -> None:
    row = connection.execute("SELECT value FROM meta WHERE key='embed_source'").fetchone()
    if row is None:
        connection.execute("INSERT INTO meta(key,value) VALUES('embed_source', ?)", (source,))
        return
    if row[0] == source:
        return
    connection.execute("DELETE FROM embeddings")
    connection.execute("UPDATE meta SET value=? WHERE key='embed_source'", (source,))


def _thread_messages(kind: str, metadata_json: str) -> list[tuple[str, str]] | None:
    if kind != "thread":
        return None
    try:
        data = json.loads(metadata_json) if metadata_json else {}
    except json.JSONDecodeError:
        return None
    blob = data.get("messages_json") if isinstance(data, dict) else None
    raw: object = None
    if isinstance(blob, str):
        try:
            raw = json.loads(blob)
        except json.JSONDecodeError:
            return None
    elif isinstance(data, dict):
        raw = data.get("messages")
    if not isinstance(raw, list):
        return None
    return [
        (str(item.get("id", "")), str(item.get("text", "")))
        for item in raw
        if isinstance(item, dict)
    ]


def generate_card(
    title: str,
    text: str,
    kind: str,
    config: Config,
    chat: Chat | None,
    connection: sqlite3.Connection | None,
    messages: list[tuple[str, str]] | None = None,
) -> tuple[Card, str]:
    if chat is None:
        return heuristic_card(
            title, text, messages=messages, connection=connection, kind=kind
        ), "heuristic"
    return llm_card(
        title,
        text,
        kind=kind,
        chat=chat,
        max_input_chars=config.cards.max_input_chars,
        connection=connection,
        messages=messages,
    )


def _write(
    connection: sqlite3.Connection, record_id: int, payload: str, method: str, norm: str
) -> None:
    connection.execute(
        "UPDATE records SET card_json=?, card_method=?, norm_text=?, derived_state='ok' WHERE id=?",
        (payload, method, norm, record_id),
    )


def _prefix(kind: str, title: str, text: str, chat: Chat | None) -> str:
    if chat is None:
        return f"This {kind} is part of {title}."[:400]
    prompt = (
        "Write a 50-100 token context prefix so this chunk is self-contained. "
        "Return plain text only.\n"
        f'<record kind="{kind}" title="{title}">\n{text[:4000]}</record>'
    )
    result = chat.complete([{"role": "user", "content": prompt}], json_mode=False, op="context")
    return result.text.strip()[:800]
