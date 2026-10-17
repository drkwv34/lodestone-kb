# SPDX-License-Identifier: Apache-2.0
"""Day 2 ingestion: one raw document per file, with a versioned hash guard."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import chain

from lodestone.config import Config
from lodestone.connectors.files import FilesConnector, RawItem

CHUNKER_VERSION = "file-v0"


def content_hash(text: str, version: str = CHUNKER_VERSION) -> str:
    normalised = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return hashlib.sha256((version + "\x00" + normalised).encode("utf-8")).hexdigest()


@dataclass
class SyncReport:
    processed: int = 0
    unchanged: int = 0
    skipped: int = 0
    llm_calls: int = 0


def upsert(connection: sqlite3.Connection, source_id: int, item: RawItem) -> bool:
    digest = content_hash(item.text)
    existing = connection.execute(
        "SELECT content_hash FROM records WHERE source_id=? AND ext_id=?", (source_id, item.ext_id)
    ).fetchone()
    if existing and existing[0] == digest:
        return False
    now = datetime.now(UTC).isoformat()
    with connection:
        connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,title,text,metadata_json,content_hash,"
            "created_at,updated_at,indexed_at) VALUES(?,?,'doc',?,?,?,?,?,?,?) "
            "ON CONFLICT(source_id,ext_id) DO UPDATE SET title=excluded.title,text=excluded.text,"
            "metadata_json=excluded.metadata_json,content_hash=excluded.content_hash,"
            "updated_at=excluded.updated_at,indexed_at=excluded.indexed_at,derived_state='pending'",
            (
                source_id,
                item.ext_id,
                item.title,
                item.text,
                json.dumps(item.metadata),
                digest,
                item.updated_at.isoformat(),
                item.updated_at.isoformat(),
                now,
            ),
        )
    return True


def sync(connection: sqlite3.Connection, config: Config) -> SyncReport:
    names = [source.name for source in config.sources]
    if len(names) != len(set(names)):
        raise ValueError("source names must be unique")
    if any(source.kind != "files" for source in config.sources):
        raise ValueError("Day 2 sync supports files sources only")
    report = SyncReport()
    for source in config.sources:
        connector = FilesConnector()
        # Validate the source before registering it; errors cannot leave a partial registry entry.
        items = connector.discover(source)
        first = next(items, None)
        with connection:
            connection.execute(
                "INSERT INTO sources(name,kind,config_json) VALUES(?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET kind=excluded.kind,"
                "config_json=excluded.config_json "
                "WHERE kind<>excluded.kind OR config_json<>excluded.config_json",
                (source.name, source.kind, source.model_dump_json()),
            )
        row = connection.execute("SELECT id FROM sources WHERE name=?", (source.name,)).fetchone()
        source_id = int(row[0])
        changed = False
        for item in chain([first] if first is not None else [], items):
            if upsert(connection, source_id, item):
                report.processed += 1
                changed = True
            else:
                report.unchanged += 1
        report.skipped += len(connector.skipped)
        if changed:
            with connection:
                connection.execute(
                    "UPDATE sources SET last_synced_at=? WHERE id=?",
                    (datetime.now(UTC).isoformat(), source_id),
                )
    return report
