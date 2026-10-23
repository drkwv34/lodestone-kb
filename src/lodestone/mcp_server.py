# SPDX-License-Identifier: Apache-2.0
"""Read-only MCP stdio server over Lodestone retrieval (FR-052)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from lodestone.config import Config
from lodestone.fusion.packet import Evidence, validate_packet
from lodestone.sdk import Lodestone
from lodestone.storage.db import open_readonly
from lodestone.storage.queries import query_log_enabled


def readonly_connection(path: Path) -> sqlite3.Connection:
    return open_readonly(path)


@contextmanager
def skip_writes() -> Iterator[None]:
    token = query_log_enabled.set(False)
    try:
        yield
    finally:
        query_log_enabled.reset(token)


def _dump_hit(hit: Evidence) -> dict[str, Any]:
    packet = hit.model_dump(by_alias=True)
    validate_packet(packet)
    return packet


def _people(kb: Lodestone, topic: str, project: str | None, limit: int) -> dict[str, Any]:
    people = [
        {"author": person.author, "score": person.score, "records": list(person.records)}
        for person in kb.who_knows(topic, project=project, limit=limit)
    ]
    return {"people": people}


def _source_stats(config: Config, project: str | None) -> dict[str, Any]:
    names = set(config.scoped_sources(project))
    connection = open_readonly(config.workspace.db_path)
    try:
        sources: list[dict[str, Any]] = []
        for source in config.sources:
            if source.name not in names:
                continue
            row = connection.execute(
                "SELECT count(*), min(r.updated_at), max(r.updated_at) FROM records r "
                "JOIN sources s ON s.id=r.source_id WHERE s.name=? AND r.tombstoned=0",
                (source.name,),
            ).fetchone()
            sources.append(
                {
                    "name": source.name,
                    "kind": source.kind,
                    "records": int(row[0] or 0) if row else 0,
                    "oldest": row[1] if row else None,
                    "newest": row[2] if row else None,
                }
            )
    finally:
        connection.close()
    projects = [
        {"name": item.name, "sources": item.sources}
        for item in config.projects
        if project is None or item.name == project
    ]
    return {"projects": projects, "sources": sources}


def create_server(config: Config, *, offline: bool = False) -> MCPServer:
    kb = Lodestone(config, offline=offline, readonly=True)
    server = MCPServer("lodestone")

    @server.tool()
    def search(
        query: str,
        project: str | None = None,
        kinds: list[str] | None = None,
        sources: list[str] | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 10,
        rerank: bool = False,
        explain: bool = False,
    ) -> dict[str, Any]:
        """LLM-free fused search unless rerank is true. Returns evidence.v1 hits."""
        with skip_writes():
            result = kb.search(
                query,
                project=project,
                kinds=kinds,
                sources=sources,
                since=since,
                until=until,
                limit=limit,
                rerank=rerank,
                explain=explain,
            )
        return {"hits": [_dump_hit(hit) for hit in result.hits], "notices": list(result.notices)}

    @server.tool()
    def grep(
        pattern: str,
        regex: bool = False,
        project: str | None = None,
        path_glob: str | None = None,
        context: int = 2,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search raw record text with a literal or regex pattern."""
        with skip_writes():
            result = kb.grep(
                pattern,
                regex=regex,
                project=project,
                path_glob=path_glob,
                context=context,
                limit=limit,
            )
        matches = [
            {
                "record_id": match.record_id,
                "uri": match.uri,
                "line": match.line,
                "text": match.text,
                "context": match.context,
            }
            for match in result.matches
        ]
        return {"matches": matches}

    @server.tool()
    def get_record(
        id: int | None = None,
        ext_id: str | None = None,
        source: str | None = None,
        include_card: bool = True,
    ) -> dict[str, Any]:
        """Fetch one record, its card, raw text and children."""
        if id is None and not ext_id:
            raise ValueError("id or ext_id is required")
        ref: int | str = int(id) if id is not None else str(ext_id)
        view = kb.get(ref, source=source)
        card = view.get("card") if include_card else None
        return {
            "record": {
                "id": view.get("id"),
                "ext_id": view.get("ext_id"),
                "source": view.get("source"),
                "kind": view.get("kind"),
                "title": view.get("title"),
                "metadata": view.get("metadata"),
            },
            "card": card,
            "raw_text": view.get("raw_text"),
            "children": view.get("children") or [],
        }

    @server.tool()
    def list_sources(project: str | None = None) -> dict[str, Any]:
        """List projects and sources with record counts and date ranges."""
        return _source_stats(config, project)

    @server.tool()
    def who_knows(topic: str, project: str | None = None, limit: int = 5) -> dict[str, Any]:
        """Rank authors of records matching a topic."""
        with skip_writes():
            return _people(kb, topic, project, limit)

    @server.tool()
    def recent(
        limit: int = 10, project: str | None = None, since: str | None = None
    ) -> dict[str, Any]:
        """Most recently updated records as evidence.v1 hits."""
        with skip_writes():
            hits = kb.recent(project=project, since=since, limit=limit)
        return {"hits": [_dump_hit(hit) for hit in hits]}

    return server


def run_stdio(config: Config, *, offline: bool = False) -> None:
    token = query_log_enabled.set(False)
    try:
        create_server(config, offline=offline).run(transport="stdio")
    finally:
        query_log_enabled.reset(token)
