# SPDX-License-Identifier: Apache-2.0
"""Planner then executor then sufficiency-bounded synthesis."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from lodestone.ask.executor import EvidenceItem, execute_calls, normalise
from lodestone.ask.planner import build_catalog, fallback_plan, plan_calls
from lodestone.ask.sufficiency import check_sufficiency
from lodestone.ask.synthesis import synthesise
from lodestone.config import Config
from lodestone.providers.chat import ChatResult, estimate_tokens

Dispatcher = Callable[[str, dict[str, Any]], Any]


@dataclass
class AskCost:
    in_tokens: int = 0
    out_tokens: int = 0
    usd: float = 0.0


@dataclass
class AskAnswer:
    text: str
    citations: list[str] = field(default_factory=list)
    rounds: int = 0
    plan: list[dict[str, Any]] = field(default_factory=list)
    cost: AskCost = field(default_factory=AskCost)
    insufficient_evidence: bool = True
    unsupported_claims: bool = False
    logged_rounds: list[list[dict[str, Any]]] = field(default_factory=list)


def _add_cost(cost: AskCost, result: ChatResult | None) -> None:
    if result is None:
        return
    cost.in_tokens += result.in_tokens or estimate_tokens("")
    cost.out_tokens += result.out_tokens or estimate_tokens(result.text)


def run_ask(
    question: str,
    *,
    config: Config,
    connection: sqlite3.Connection,
    handler: Dispatcher,
    chat: Any | None,
    project: str | None = None,
    max_rounds: int | None = None,
) -> AskAnswer:
    rounds_limit = max_rounds or config.ask.max_rounds
    catalog = build_catalog(connection, config)
    plan, planned = plan_calls(question, catalog, chat)
    cost = AskCost()
    _add_cost(cost, planned)
    collected: list[EvidenceItem] = []
    logged: list[list[dict[str, Any]]] = []
    draft = ""
    citations: list[str] = []
    unsupported = False
    calls = plan
    used_rounds = 0
    for round_index in range(max(1, rounds_limit)):
        used_rounds = round_index + 1
        if project:
            for call in calls:
                args = dict(call.get("args") or {})
                args.setdefault("project", project)
                call["args"] = args
        logged.append(list(calls))
        collected = normalise(collected + execute_calls(calls, handler))
        if not collected:
            return AskAnswer(
                text="",
                citations=[],
                rounds=used_rounds,
                plan=plan,
                cost=cost,
                insufficient_evidence=True,
                logged_rounds=logged,
            )
        draft, citations, unsupported, synthesised = synthesise(question, collected, chat)
        _add_cost(cost, synthesised)
        if round_index >= rounds_limit - 1:
            break
        sufficient, follow_up, checked = check_sufficiency(question, collected, draft, chat)
        _add_cost(cost, checked)
        if sufficient:
            break
        query = follow_up or question
        calls = fallback_plan(query)
        if calls:
            first = dict(calls[0].get("args") or {})
            first["query"] = query
            calls[0]["args"] = first
    return AskAnswer(
        text=draft,
        citations=citations,
        rounds=used_rounds,
        plan=plan,
        cost=cost,
        insufficient_evidence=False,
        unsupported_claims=unsupported,
        logged_rounds=logged,
    )
