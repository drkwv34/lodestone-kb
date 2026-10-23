# SPDX-License-Identifier: Apache-2.0
"""Typed Lodestone facade over workspace operations; no global state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lodestone.config import Config, load_config
from lodestone.experts import Expert
from lodestone.fusion.packet import Evidence
from lodestone.ingest.pipeline import SyncReport
from lodestone.lanes.fts import LaneName
from lodestone.storage.db import open_readonly
from lodestone.storage.queries import query_log_enabled
from lodestone.workspace import (
    get_workspace,
    grep_workspace,
    initialise,
    recent_workspace,
    search_result,
    stats_workspace,
    sync_workspace,
    who_knows_workspace,
)


@dataclass(frozen=True)
class Cost:
    in_tokens: int = 0
    out_tokens: int = 0
    usd: float = 0.0


@dataclass(frozen=True)
class SearchResult:
    hits: list[Evidence]
    notices: list[str]
    timing_ms: dict[str, float]
    cost: Cost


@dataclass(frozen=True)
class GrepMatch:
    record_id: int
    uri: str
    line: int
    text: str
    context: str


@dataclass(frozen=True)
class GrepResult:
    matches: list[GrepMatch]
    notices: list[str]


@dataclass(frozen=True)
class Stats:
    records: int
    sources: int
    schema_version: int
    query_log: int
    store_queries: bool


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    rounds: int = 0
    plan: list[dict[str, Any]] = field(default_factory=list)
    cost: Cost = field(default_factory=Cost)
    insufficient_evidence: bool = True
    unsupported_claims: bool = False


def _evidence(payload: dict[str, object]) -> Evidence:
    return Evidence.model_validate(payload)


def _int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("expected int")
    return value


class Lodestone:
    """Open a workspace from a config path, directory, or Config object."""

    def __init__(
        self,
        config: Config,
        *,
        offline: bool = False,
        path: Path | None = None,
        readonly: bool = False,
    ) -> None:
        self._config = config
        self._offline = offline
        self._path = path
        self._readonly = readonly

    @classmethod
    def open(
        cls, config: str | Path | Config = "lodestone.toml", *, offline: bool = False
    ) -> Lodestone:
        if isinstance(config, Config):
            return cls(config, offline=offline)
        path = Path(config)
        if path.is_dir() or path.suffix != ".toml":
            directory = path if path.suffix != ".toml" else path.parent
            initialise(directory)
            path = directory / "lodestone.toml"
        return cls(load_config(path), offline=offline, path=path)

    def sync(
        self, sources: list[str] | None = None, *, prune: bool = False, dry_run: bool = False
    ) -> SyncReport:
        del dry_run
        return sync_workspace(self._config, sources=sources, prune=prune, offline=self._offline)

    def search(
        self,
        query: str,
        *,
        project: str | None = None,
        kinds: list[str] | None = None,
        sources: list[str] | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 10,
        rerank: bool | None = None,
        decay: bool = True,
        explain: bool = False,
        authors: list[str] | None = None,
        metadata: dict[str, str] | None = None,
        lane: LaneName | None = None,
        regex: bool = False,
        provider: str | None = None,
    ) -> SearchResult:
        result = search_result(
            self._config,
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
            offline=self._offline,
            decay=decay,
            explain=explain,
            regex=regex,
            rerank=rerank,
            provider=provider,
        )
        hits = (
            [_evidence(packet) for packet in result.packets]
            if result.packets
            else [
                Evidence(
                    schema="evidence.v1",
                    id=hit.id,
                    source=hit.source,
                    kind=hit.kind,
                    title=hit.title,
                    uri=hit.uri,
                    snippet=hit.snippet,
                    score=hit.score,
                    updated_at=hit.updated_at,
                )
                for hit in result.hits
            ]
        )
        return SearchResult(hits, result.notices, {"search": 0.0}, Cost())

    def grep(
        self,
        pattern: str,
        *,
        regex: bool = False,
        project: str | None = None,
        path_glob: str | None = None,
        context: int = 2,
        limit: int = 20,
    ) -> GrepResult:
        result = grep_workspace(
            self._config,
            pattern,
            regex=regex,
            project=project,
            path_glob=path_glob,
            context=context,
            limit=limit,
        )
        matches = [
            GrepMatch(
                record_id=_int(item["record_id"]),
                uri=str(item.get("uri") or ""),
                line=_int(item["line"]),
                text=str(item.get("text") or ""),
                context=str(item.get("context") or ""),
            )
            for item in result.matches
        ]
        return GrepResult(matches, result.notices)

    def get(self, ref: int | str, *, source: str | None = None) -> dict[str, Any]:
        return get_workspace(self._config, str(ref), source)

    def who_knows(self, topic: str, *, project: str | None = None, limit: int = 5) -> list[Expert]:
        return who_knows_workspace(self._config, topic, project=project, limit=limit)

    def recent(
        self,
        *,
        project: str | None = None,
        since: str | None = None,
        limit: int = 10,
    ) -> list[Evidence]:
        result = recent_workspace(self._config, project=project, since=since, limit=limit)
        return [_evidence(packet) for packet in result.packets]

    def _dispatch(self, tool: str, args: dict[str, Any]) -> object:
        if tool == "search":
            query = str(args.get("query") or "")
            return self.search(
                query,
                project=args.get("project") if isinstance(args.get("project"), str) else None,
                kinds=args.get("kinds") if isinstance(args.get("kinds"), list) else None,
                sources=args.get("sources") if isinstance(args.get("sources"), list) else None,
                since=args.get("since") if isinstance(args.get("since"), str) else None,
                until=args.get("until") if isinstance(args.get("until"), str) else None,
                limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 10,
                rerank=bool(args.get("rerank")) if args.get("rerank") is not None else False,
                explain=bool(args.get("explain")) if args.get("explain") is not None else False,
            )
        if tool == "grep":
            pattern = str(args.get("pattern") or args.get("query") or "")
            return self.grep(
                pattern,
                regex=bool(args.get("regex")),
                project=args.get("project") if isinstance(args.get("project"), str) else None,
                path_glob=args.get("path_glob") if isinstance(args.get("path_glob"), str) else None,
                context=int(args["context"]) if isinstance(args.get("context"), int) else 2,
                limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 20,
            )
        if tool == "who_knows":
            topic = str(args.get("topic") or args.get("query") or "")
            return self.who_knows(
                topic,
                project=args.get("project") if isinstance(args.get("project"), str) else None,
                limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 5,
            )
        if tool == "recent":
            return self.recent(
                project=args.get("project") if isinstance(args.get("project"), str) else None,
                since=args.get("since") if isinstance(args.get("since"), str) else None,
                limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 10,
            )
        raise ValueError(f"unknown tool: {tool}")

    def ask(
        self,
        question: str,
        *,
        project: str | None = None,
        max_rounds: int | None = None,
        provider: str | None = None,
    ) -> Answer:
        from lodestone.ask import run_ask
        from lodestone.providers import make_chat

        guarded = self._offline or self._config.offline
        token = query_log_enabled.set(False) if self._readonly else None
        connection = open_readonly(self._config.workspace.db_path)
        try:
            chat = make_chat(self._config, provider, offline=guarded)
            result = run_ask(
                question,
                config=self._config,
                connection=connection,
                handler=self._dispatch,
                chat=chat,
                project=project,
                max_rounds=max_rounds,
            )
        finally:
            connection.close()
            if token is not None:
                query_log_enabled.reset(token)
        return Answer(
            text=result.text,
            citations=list(result.citations),
            rounds=result.rounds,
            plan=list(result.plan),
            cost=Cost(result.cost.in_tokens, result.cost.out_tokens, result.cost.usd),
            insufficient_evidence=result.insufficient_evidence,
            unsupported_claims=result.unsupported_claims,
        )

    def stats(self) -> Stats:
        payload = stats_workspace(self._config)
        return Stats(
            records=_int(payload["records"]),
            sources=_int(payload["sources"]),
            schema_version=_int(payload["schema_version"]),
            query_log=_int(payload["query_log"]),
            store_queries=bool(payload["store_queries"]),
        )

    def close(self) -> None:
        return

    def __enter__(self) -> Lodestone:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
