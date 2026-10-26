# SPDX-License-Identifier: Apache-2.0
"""Lexical thread upsert: parent + bursts in one transaction, cards later."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from lodestone.config import Config
from lodestone.connectors.files import RawItem
from lodestone.ingest.bursts import qualifying_bursts
from lodestone.ingest.hashing import THREAD_VERSION, content_hash
from lodestone.storage.terms import idf as term_idf


def ingest_thread_lexical(
    connection: sqlite3.Connection, source_id: int, item: RawItem, config: Config
) -> tuple[bool, int]:
    version = THREAD_VERSION + ":thread"
    digest = content_hash(item.text, version)
    existing = connection.execute(
        "SELECT id,content_hash,tombstoned,derived_state FROM records "
        "WHERE source_id=? AND ext_id=?",
        (source_id, item.ext_id),
    ).fetchone()
    if existing and existing[1] == digest and not existing[2]:
        return False, int(existing[0])
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
        write_bursts(connection, source_id, parent_id, item, config, version, updated, now)
    return True, parent_id


def write_bursts(
    connection: sqlite3.Connection,
    source_id: int,
    parent_id: int,
    item: RawItem,
    config: Config,
    version: str,
    updated: str,
    now: str,
) -> None:
    prefix = item.title
    kept = qualifying_bursts(
        item.messages or (), config.bursts, lambda term: term_idf(connection, term)
    )
    for seq, burst in enumerate(kept):
        metadata = {
            **item.metadata,
            "message_ids": json.dumps([message.id for message in burst.messages]),
            "reactions": burst.reactions,
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


def refresh_burst_prefixes(connection: sqlite3.Connection, parent_id: int, title: str) -> None:
    row = connection.execute("SELECT card_json FROM records WHERE id=?", (parent_id,)).fetchone()
    prefix = title
    if row and row[0]:
        try:
            question = json.loads(row[0]).get("question")
        except json.JSONDecodeError:
            question = None
        if isinstance(question, str) and question.strip():
            prefix = question.strip()
    connection.execute(
        "UPDATE records SET context_prefix=? WHERE parent_id=? AND kind='burst'",
        (prefix, parent_id),
    )
