# SPDX-License-Identifier: Apache-2.0
"""Small real SQLite fixtures shared by lexical integration tests."""

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
        self, text: str, *, title: str = "", source: str = "wiki", kind: str = "doc"
    ) -> int:
        self.counter += 1
        self.connection.execute(
            "INSERT OR IGNORE INTO sources(name,kind,config_json) VALUES(?,'files','{}')", (source,)
        )
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE name=?", (source,)
        ).fetchone()[0]
        cursor = self.connection.execute(
            "INSERT INTO records(source_id,ext_id,kind,title,text,content_hash,created_at,"
            "updated_at,indexed_at) VALUES(?,?,?,?,?,'h','2026-10-17','2026-10-17','2026-10-17')",
            (source_id, f"file-{self.counter}.txt", kind, title, text),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid


@pytest.fixture
def record_factory(database: sqlite3.Connection) -> RecordFactory:
    return RecordFactory(database)
