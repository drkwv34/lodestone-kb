# SPDX-License-Identifier: Apache-2.0
"""Small real SQLite fixtures shared by lexical integration tests."""

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from lodestone.providers.offline import set_offline
from lodestone.storage.db import open_database


@pytest.fixture(autouse=True)
def _reset_offline() -> Iterator[None]:
    set_offline(False)
    yield
    set_offline(False)


@pytest.fixture
def database(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = open_database(tmp_path / "index.db")
    yield connection
    connection.close()


@dataclass
class RecordFactory:
    connection: sqlite3.Connection
    counter: int = 0

    def __call__(
        self,
        text: str,
        *,
        title: str = "",
        source: str = "wiki",
        kind: str = "doc",
        parent_id: int | None = None,
        seq: int = 0,
        author: str | None = None,
        authors: list[str] | None = None,
        updated_at: str = "2026-10-17",
        metadata: dict[str, str] | None = None,
        ext_id: str | None = None,
    ) -> int:
        self.counter += 1
        self.connection.execute(
            "INSERT OR IGNORE INTO sources(name,kind,config_json) VALUES(?,'files','{}')", (source,)
        )
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE name=?", (source,)
        ).fetchone()[0]
        cursor = self.connection.execute(
            "INSERT INTO records(source_id,ext_id,parent_id,kind,seq,title,text,author,"
            "authors_json,metadata_json,content_hash,created_at,updated_at,indexed_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,'h',?,?,?)",
            (
                source_id,
                ext_id or f"file-{self.counter}.txt",
                parent_id,
                kind,
                seq,
                title,
                text,
                author,
                json.dumps(authors or ([author] if author else [])),
                json.dumps(metadata or {}),
                updated_at,
                updated_at,
                updated_at,
            ),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid


@pytest.fixture
def record_factory(database: sqlite3.Connection) -> RecordFactory:
    return RecordFactory(database)
