# SPDX-License-Identifier: Apache-2.0
"""Workspace setup and connection lifetimes for local operations."""

import sqlite3
from pathlib import Path

from lodestone.config import DEFAULT_TOML, Config, Source, load_config
from lodestone.config_io import registry_text, replace_config
from lodestone.ingest.pipeline import SyncReport, sync
from lodestone.lanes.fts import Hit, LaneName, search
from lodestone.storage.db import SCHEMA_VERSION, StorageError, inspect_database, open_database
from lodestone.storage.registry import reconcile


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


def sync_workspace(
    config: Config,
    *,
    sources: list[str] | None = None,
    project: str | None = None,
    prune: bool = False,
) -> SyncReport:
    connection = open_database(config.workspace.db_path)
    try:
        return sync(connection, config, sources=sources, project=project, prune=prune)
    finally:
        connection.close()


def search_workspace(
    config: Config,
    query: str,
    *,
    project: str | None = None,
    lane: LaneName = "fts_raw",
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    limit: int = 10,
) -> list[Hit]:
    sources = config.scoped_sources(project, sources)
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


def source_list(config: Config, project: str | None = None) -> list[dict[str, object]]:
    names = config.scoped_sources(project)
    return [source.model_dump(mode="json") for source in config.sources if source.name in names]


def update_source(
    path: Path, name: str, *, source: Source | None = None, project: str | None = None
) -> None:
    """Persist a registry mutation and cascade removal through the existing SQLite schema."""
    config = load_config(path)
    scope = config.scoped_sources(project)
    target = project if project is not None else config.workspace.default_project
    if source is None:
        if name not in scope:
            raise ValueError("source is not in selected project")
        config.sources = [item for item in config.sources if item.name != name]
        for member in config.projects:
            member.sources = [item for item in member.sources if item != name]
    else:
        if any(item.name == name for item in config.sources):
            raise ValueError("source already exists")
        config.sources.append(source)
        next(item for item in config.projects if item.name == target).sources.append(name)
    text = registry_text(path, config)
    connection = open_database(config.workspace.db_path)
    try:
        # A failed file replacement rolls back all registry and dependent data mutations.
        with connection:
            reconcile(connection, config)
            replace_config(path, text)
    finally:
        connection.close()
