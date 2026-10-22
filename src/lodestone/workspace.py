# SPDX-License-Identifier: Apache-2.0
"""Workspace setup and connection lifetimes for local operations."""

import sqlite3
import time
from pathlib import Path

from lodestone.config import DEFAULT_TOML, Config, Prices, Source, load_config
from lodestone.config_io import registry_text, replace_config
from lodestone.experts import Expert, packets_for, recent, who_knows
from lodestone.fusion.pipeline import fused_search
from lodestone.ingest.embeddings import reindex_vectors
from lodestone.ingest.pipeline import SyncReport, sync
from lodestone.lanes.fts import Hit, LaneName, search
from lodestone.lanes.grep import GrepError
from lodestone.lanes.grep import search as grep_search
from lodestone.lanes.result import SearchResult
from lodestone.lanes.scope import Scope
from lodestone.lanes.vec import search as vec_search
from lodestone.providers import make_chat
from lodestone.providers.offline import offline_scope
from lodestone.storage.costs import summarise
from lodestone.storage.db import SCHEMA_VERSION, StorageError, inspect_database, open_database
from lodestone.storage.queries import count_queries, log_query
from lodestone.storage.records import get_record
from lodestone.storage.registry import reconcile
from lodestone.vectors.embedder import make_embedder


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
    provider: str | None = None,
    refresh_cards: bool = False,
    offline: bool = False,
) -> SyncReport:
    guarded = offline or config.offline
    connection = open_database(config.workspace.db_path)
    try:
        with offline_scope(guarded):
            chat = make_chat(config, provider, offline=guarded)
            embedder = make_embedder(config, offline=guarded)
            try:
                return sync(
                    connection,
                    config,
                    sources=sources,
                    project=project,
                    prune=prune,
                    chat=chat,
                    refresh_cards=refresh_cards,
                    embedder=embedder,
                )
            finally:
                for client in (chat, embedder):
                    closer = getattr(client, "close", None)
                    if callable(closer):
                        closer()
    finally:
        connection.close()


def cost_workspace(config: Config) -> dict[str, object]:
    connection = sqlite3.connect(f"{config.workspace.db_path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        prices = config.llm.prices if config.llm is not None else Prices()
        return summarise(connection, prices)
    finally:
        connection.close()


def get_workspace(config: Config, ref: str, source: str | None = None) -> dict[str, object]:
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return get_record(connection, ref, source)
    finally:
        connection.close()


def search_workspace(
    config: Config,
    query: str,
    *,
    project: str | None = None,
    lane: LaneName | None = None,
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    authors: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
    metadata: dict[str, str] | None = None,
    limit: int = 10,
    offline: bool = False,
    decay: bool = True,
    explain: bool = False,
    regex: bool = False,
    rerank: bool | None = None,
    provider: str | None = None,
) -> list[Hit]:
    return search_result(
        config,
        query,
        project=project,
        lane=lane,
        sources=sources,
        kinds=kinds,
        authors=authors,
        since=since,
        until=until,
        metadata=metadata,
        limit=limit,
        offline=offline,
        decay=decay,
        explain=explain,
        regex=regex,
        rerank=rerank,
        provider=provider,
    ).hits


def search_result(
    config: Config,
    query: str,
    *,
    project: str | None = None,
    lane: LaneName | None = None,
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
    authors: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
    metadata: dict[str, str] | None = None,
    limit: int = 10,
    offline: bool = False,
    decay: bool = True,
    explain: bool = False,
    regex: bool = False,
    rerank: bool | None = None,
    provider: str | None = None,
) -> SearchResult:
    sources = config.scoped_sources(project, sources)
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    scope = Scope(
        sources=sources, kinds=kinds, authors=authors, since=since, until=until, metadata=metadata
    )
    started = time.monotonic()
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        result = _search_open(
            connection,
            config,
            query,
            lane=lane,
            scope=scope,
            limit=limit,
            offline=offline,
            decay=decay,
            explain=explain,
            regex=regex,
            rerank=rerank,
            provider=provider,
        )
    finally:
        connection.close()
    _log_query(
        config,
        query=query,
        project=project,
        lanes=result.lane or (lane or "fused"),
        results=len(result.hits),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
    return result


def _search_open(
    connection: sqlite3.Connection,
    config: Config,
    query: str,
    *,
    lane: LaneName | None,
    scope: Scope,
    limit: int,
    offline: bool,
    decay: bool,
    explain: bool,
    regex: bool,
    rerank: bool | None,
    provider: str | None,
) -> SearchResult:
    if lane is None:
        guarded = offline or config.offline
        with offline_scope(guarded):
            embedder = make_embedder(config, offline=guarded)
            chat = None
            want = config.retrieval.rerank if rerank is None else rerank
            if want:
                chosen = provider
                if chosen is None and config.llm is not None and not guarded:
                    chosen = "config"
                chat = make_chat(config, chosen, offline=guarded)
            try:
                return fused_search(
                    connection,
                    config,
                    query,
                    scope=scope,
                    limit=limit,
                    decay=decay,
                    explain=explain,
                    regex=regex,
                    include_grep=regex,
                    embedder=embedder,
                    rerank=rerank,
                    chat=chat,
                )
            finally:
                for client in (embedder, chat):
                    closer = getattr(client, "close", None)
                    if callable(closer):
                        closer()
    if lane == "grep":
        try:
            return grep_search(connection, query, regex=regex, scope=scope, limit=limit)
        except GrepError as exc:
            raise ValueError(str(exc)) from exc
    if lane == "vec_card" or lane == "vec_chunk":
        guarded = offline or config.offline
        with offline_scope(guarded):
            embedder = make_embedder(config, offline=guarded)
            try:
                return vec_search(
                    connection,
                    query,
                    lane=lane,
                    embedder=embedder,
                    scope=scope,
                    limit=limit,
                )
            finally:
                closer = getattr(embedder, "close", None)
                if callable(closer):
                    closer()
    hits = search(
        connection,
        query,
        lane=lane,
        scope=scope,
        limit=limit,
        rare_idf=config.retrieval.rare_idf,
        rare_df_ratio=config.retrieval.rare_df_ratio,
    )
    return SearchResult(hits, [], lane)


def _log_query(
    config: Config, *, query: str, project: str | None, lanes: str, results: int, latency_ms: int
) -> None:
    connection = open_database(config.workspace.db_path)
    try:
        with connection:
            log_query(
                connection,
                query=query,
                project=project or config.workspace.default_project,
                lanes=lanes,
                results=results,
                latency_ms=latency_ms,
                store_text=config.log.store_queries,
            )
    finally:
        connection.close()


def grep_workspace(
    config: Config,
    pattern: str,
    *,
    regex: bool = False,
    project: str | None = None,
    sources: list[str] | None = None,
    path_glob: str | None = None,
    context: int = 2,
    limit: int = 20,
) -> SearchResult:
    started = time.monotonic()
    scope = Scope(sources=config.scoped_sources(project, sources))
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        try:
            result = grep_search(
                connection, pattern, regex=regex, scope=scope, limit=limit, context=context
            )
        except GrepError as exc:
            raise ValueError(str(exc)) from exc
        if path_glob:
            from fnmatch import fnmatch

            kept = [
                (hit, match)
                for hit, match in zip(result.hits, result.matches, strict=False)
                if fnmatch(hit.ext_id, path_glob) or fnmatch(hit.uri, path_glob)
            ]
            result.hits = [item[0] for item in kept]
            result.matches = [item[1] for item in kept]
    finally:
        connection.close()
    _log_query(
        config,
        query=pattern,
        project=project,
        lanes="grep",
        results=len(result.hits),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
    return result


def who_knows_workspace(
    config: Config, topic: str, *, project: str | None = None, limit: int = 5
) -> list[Expert]:
    sources = config.scoped_sources(project)
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    started = time.monotonic()
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        people = who_knows(connection, config, topic, scope=Scope(sources=sources), limit=limit)
    finally:
        connection.close()
    _log_query(
        config,
        query=topic,
        project=project,
        lanes="who_knows",
        results=len(people),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
    return people


def recent_workspace(
    config: Config,
    *,
    project: str | None = None,
    since: str | None = None,
    limit: int = 10,
    sources: list[str] | None = None,
    kinds: list[str] | None = None,
) -> SearchResult:
    sources = config.scoped_sources(project, sources)
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    started = time.monotonic()
    scope = Scope(sources=sources, kinds=kinds, since=since)
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        hits = recent(connection, scope, limit=limit)
        packets = packets_for(connection, hits)
    finally:
        connection.close()
    _log_query(
        config,
        query="",
        project=project,
        lanes="recent",
        results=len(hits),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
    return SearchResult(hits, [], "recent", packets)


def stats_workspace(config: Config) -> dict[str, object]:
    path = config.workspace.db_path
    if inspect_database(path) != SCHEMA_VERSION:
        raise StorageError("Database requires migration; run lodestone init")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        records = int(
            connection.execute("SELECT count(*) FROM records WHERE tombstoned=0").fetchone()[0]
        )
        sources = int(connection.execute("SELECT count(*) FROM sources").fetchone()[0])
        queries = count_queries(connection)
    finally:
        connection.close()
    return {
        "records": records,
        "sources": sources,
        "schema_version": SCHEMA_VERSION,
        "query_log": queries,
        "store_queries": config.log.store_queries,
    }


def reindex_workspace(config: Config, *, lanes: list[str], offline: bool = False) -> dict[str, int]:
    unknown = [lane for lane in lanes if lane != "vec"]
    if unknown:
        raise ValueError("only --lanes vec is supported")
    guarded = offline or config.offline
    connection = open_database(config.workspace.db_path)
    try:
        with offline_scope(guarded):
            embedder = make_embedder(config, offline=guarded)
            try:
                if embedder is None:
                    raise ValueError(
                        "embeddings are disabled; set embed.provider or pass --offline"
                    )
                before = int(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0])
                with connection:
                    written = reindex_vectors(
                        connection,
                        embedder,
                        config.embed.source,
                        batch_size=config.embed.batch_size,
                    )
                after = int(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0])
                records = int(
                    connection.execute(
                        "SELECT count(*) FROM records WHERE tombstoned=0"
                    ).fetchone()[0]
                )
                return {
                    "before": before,
                    "after": after,
                    "written": written,
                    "records": records,
                }
            finally:
                closer = getattr(embedder, "close", None)
                if callable(closer):
                    closer()
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
