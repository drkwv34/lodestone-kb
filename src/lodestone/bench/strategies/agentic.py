# SPDX-License-Identifier: Apache-2.0
"""agentic-ask: ask pipeline; retrieval is the union of cited evidence."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from lodestone.ask.executor import collect_items, normalise
from lodestone.ask.pipeline import run_ask
from lodestone.bench.metrics import collapse_parents
from lodestone.bench.strategies.lodestone import HYBRID_LANES, LodestoneStrategy
from lodestone.config import load_config
from lodestone.providers import Chat, FakeLLM, make_chat
from lodestone.storage.db import open_readonly
from lodestone.workspace import grep_workspace, recent_workspace, search_result, who_knows_workspace


def _parent_ext_id(connection: sqlite3.Connection, record_id: int) -> str | None:
    row = connection.execute(
        "SELECT r.ext_id, p.ext_id FROM records r LEFT JOIN records p ON p.id=r.parent_id "
        "WHERE r.id=?",
        (record_id,),
    ).fetchone()
    if row is None:
        return None
    return str(row[1] or row[0])


class AgenticAsk(LodestoneStrategy):
    name = "agentic-ask"

    def __init__(self, directory: Path, chat: Chat | None = None) -> None:
        super().__init__(
            directory,
            name="agentic-ask",
            lanes=HYBRID_LANES,
            embed="hash",
            rerank=False,
            provider="fake",
            chat=chat,
        )
        self.last_answer = ""

    def retrieve(self, question: str, k: int) -> list[str]:
        config = load_config(self.config_path)
        captured: list[object] = []

        def handler(tool: str, args: dict[str, Any]) -> object:
            result: object
            if tool == "search":
                result = search_result(
                    config,
                    str(args.get("query") or ""),
                    project=args.get("project") if isinstance(args.get("project"), str) else None,
                    limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 10,
                    offline=True,
                    decay=True,
                    rerank=False,
                )
            elif tool == "grep":
                result = grep_workspace(
                    config,
                    str(args.get("pattern") or args.get("query") or ""),
                    regex=bool(args.get("regex")),
                    project=args.get("project") if isinstance(args.get("project"), str) else None,
                    limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 20,
                )
            elif tool == "who_knows":
                result = who_knows_workspace(
                    config,
                    str(args.get("topic") or args.get("query") or ""),
                    project=args.get("project") if isinstance(args.get("project"), str) else None,
                    limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 5,
                )
            elif tool == "recent":
                result = recent_workspace(
                    config,
                    project=args.get("project") if isinstance(args.get("project"), str) else None,
                    since=args.get("since") if isinstance(args.get("since"), str) else None,
                    limit=int(args["limit"]) if isinstance(args.get("limit"), int) else 10,
                )
            else:
                raise ValueError(f"unknown tool: {tool}")
            captured.append(result)
            return result

        provider: Chat = self.chat if self.chat is not None else FakeLLM()
        if self.chat is None:
            created = make_chat(config, "fake", offline=True)
            if created is not None:
                provider = created
        ids: list[str] = []
        answer_text = ""
        in_tokens = 0
        out_tokens = 0
        connection = open_readonly(config.workspace.db_path)
        try:
            answer = run_ask(
                question,
                config=config,
                connection=connection,
                handler=handler,
                chat=provider,
            )
            items = normalise([item for result in captured for item in collect_items(result)])
            wanted = set(answer.citations)
            chosen = [item for item in items if item.label in wanted] or items
            for item in chosen:
                ext_id = _parent_ext_id(connection, item.record_id)
                if ext_id:
                    ids.append(ext_id)
            answer_text = answer.text
            in_tokens = answer.cost.in_tokens
            out_tokens = answer.cost.out_tokens
        finally:
            connection.close()
        self.last_answer = answer_text
        self.last_in_tokens = in_tokens
        self.last_out_tokens = out_tokens
        return collapse_parents(ids)[:k]

    def answer(self, question: str) -> str:
        if not self.last_answer:
            self.retrieve(question, 20)
        return self.last_answer
