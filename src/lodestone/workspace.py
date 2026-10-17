# SPDX-License-Identifier: Apache-2.0
"""Workspace setup and connection lifetimes for local operations."""

import sqlite3
from pathlib import Path

from lodestone.config import DEFAULT_TOML, Config, load_config
from lodestone.ingest.pipeline import SyncReport, sync
from lodestone.lanes.fts import Hit, LaneName, search
from lodestone.storage.db import SCHEMA_VERSION, StorageError, inspect_database, open_database


def initialise(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "lodestone.toml"
    existed = config_path.exists()
    if not existed:
        try:
            with config_path.open("x", encoding="utf-8") as stream:
                stream.write(DEFAULT_TOML)
        except FileExistsError:
            existed = True
    config = load_config(config_path)
    database_existed = config.workspace.db_path.exists()
    connection = open_database(config.workspace.db_path)
    connection.close()
    return existed and database_existed


def sync_workspace(config: Config) -> SyncReport:
    connection = open_database(config.workspace.db_path)
    try:
        return sync(connection, config)
    finally:
        connection.close()


def search_workspace(
    config: Config,
    query: str,
    *,
    lane: LaneName = "fts_raw",
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    limit: int = 10,
) -> list[Hit]:
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return search(
            connection,
            query,
            lane=lane,
            sources=sources,
            kinds=kinds,
            limit=limit,
            rare_idf=config.retrieval.rare_idf,
            rare_df_ratio=config.retrieval.rare_df_ratio,
        )
    finally:
        connection.close()
