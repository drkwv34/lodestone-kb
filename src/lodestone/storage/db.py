# SPDX-License-Identifier: Apache-2.0
"""Forward-only transactional migrations and runtime capability probes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1
MIGRATIONS = Path(__file__).parent / "migrations"


class StorageError(RuntimeError):
    """Unsupported runtime, migration failure, or incompatible database."""


def probe_fts5() -> None:
    try:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE fts_probe USING fts5(text, "
                "tokenize=\"unicode61 remove_diacritics 2 tokenchars '_-'\")"
            )
            connection.execute("INSERT INTO fts_probe VALUES (?)", ("ERR_MANIFEST_TIMEOUT",))
            row = connection.execute(
                "SELECT count(*) FROM fts_probe WHERE fts_probe MATCH ?",
                ('"ERR_MANIFEST_TIMEOUT"',),
            ).fetchone()
            if row != (1,):
                raise StorageError("FTS5 probe returned an unexpected result")
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise StorageError(
            "FTS5 unavailable: install a python.org Python build with SQLite FTS5 support "
            "or use pysqlite3-binary in a compatible environment"
        ) from exc


def schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def check_version(connection: sqlite3.Connection) -> int:
    version = schema_version(connection)
    if version > SCHEMA_VERSION:
        raise StorageError(
            f"Database schema {version} is newer than supported schema {SCHEMA_VERSION}; "
            "upgrade Lodestone (downgrades are refused)"
        )
    return version


def migrate(connection: sqlite3.Connection, directory: Path = MIGRATIONS) -> None:
    current = check_version(connection)
    if connection.in_transaction:
        raise StorageError("Migrations require a connection without an active transaction")
    migrations = sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    for version in range(current + 1, SCHEMA_VERSION + 1):
        matches = [path for path in migrations if int(path.name[:4]) == version]
        if len(matches) != 1:
            raise StorageError(f"Expected exactly one migration for schema {version}")
        sql = matches[0].read_text(encoding="utf-8")
        try:
            connection.executescript(
                f"BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version={version};\nCOMMIT;"
            )
        except sqlite3.Error as exc:
            connection.rollback()
            raise StorageError(f"Migration {matches[0].name} failed: {exc}") from exc


def open_database(path: Path) -> sqlite3.Connection:
    probe_fts5()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        check_version(connection)  # Refuse newer databases before changing any persistent setting.
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        migrate(connection)
    except (sqlite3.Error, StorageError):
        connection.close()
        raise
    return connection


def inspect_database(path: Path) -> int:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return check_version(connection)
    finally:
        connection.close()
