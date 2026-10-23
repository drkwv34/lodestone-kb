# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from lodestone.ask.pipeline import run_ask
from lodestone.ask.planner import fallback_plan, validate_plan
from lodestone.config import load_config
from lodestone.providers.chat import ChatResult
from lodestone.providers.fake import FakeLLM
from lodestone.sdk import Lodestone
from lodestone.storage.db import open_readonly
from tests.helpers import synced_workspace


class NeverSufficient(FakeLLM):
    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool = False, op: str = "chat"
    ) -> ChatResult:
        blob = "\n".join(message.get("content", "") for message in messages).lower()
        if "sufficient" in blob:
            self.calls.append(messages)
            return ChatResult(
                text="NEED: more about restore stalls",
                model=self.model,
                in_tokens=8,
                out_tokens=8,
                latency_ms=0,
                ok=True,
            )
        return super().complete(messages, json_mode=json_mode, op=op)


def _run(
    tmp_path: Path,
    question: str,
    chat: FakeLLM,
    *,
    max_rounds: int = 1,
) -> object:
    config_path = synced_workspace(tmp_path)
    config = load_config(config_path)
    kb = Lodestone(config, offline=True)
    connection = open_readonly(config.workspace.db_path)
    try:
        return run_ask(
            question,
            config=config,
            connection=connection,
            handler=kb._dispatch,
            chat=chat,
            max_rounds=max_rounds,
        )
    finally:
        connection.close()


def test_fr_054_planner_fallback_on_malformed_plan() -> None:
    question = "find ERR_MANIFEST_TIMEOUT"
    assert fallback_plan(question)[0]["tool"] == "search"
    assert any(call["tool"] == "grep" for call in fallback_plan(question))
    malformed = validate_plan("not-json", question)
    assert malformed[0]["tool"] == "search"
    empty = validate_plan({"calls": []}, question)
    assert empty[0]["args"]["query"] == question
    dropped = validate_plan({"calls": [{"tool": "drop_table", "args": {}}]}, "plain question")
    assert dropped[0]["tool"] == "search"
    assert all(call["tool"] in {"search", "grep", "who_knows", "recent"} for call in dropped)
    valid = validate_plan(
        {"calls": [{"tool": "search", "args": {"query": "x", "bogus": 1}}]},
        "x",
    )
    assert "bogus" not in valid[0]["args"]


def test_fr_053_citations_only_retrieved_ids(tmp_path: Path) -> None:
    chat = FakeLLM(
        script=[
            json.dumps(
                {
                    "calls": [
                        {"tool": "search", "args": {"query": "ERR_MANIFEST_TIMEOUT"}},
                        {"tool": "grep", "args": {"pattern": "ERR_MANIFEST_TIMEOUT"}},
                        {"tool": "who_knows", "args": {"topic": "manifest"}},
                        {"tool": "recent", "args": {"limit": 2}},
                    ]
                }
            ),
            "The stall is documented [E1] and also [E99] invented.",
        ]
    )
    answer = _run(tmp_path, "Why does restore stall?", chat, max_rounds=1)
    assert not answer.insufficient_evidence
    assert "[E99]" not in answer.text
    assert "E1" in answer.citations
    for label in answer.citations:
        assert label.startswith("E")


def test_fr_053_empty_evidence_refuses(tmp_path: Path) -> None:
    from lodestone.sdk import Cost, SearchResult

    config_path = synced_workspace(tmp_path)
    config = load_config(config_path)
    kb = Lodestone(config, offline=True)

    def empty(_tool: str, _args: dict[str, object]) -> SearchResult:
        return SearchResult(hits=[], notices=[], timing_ms={}, cost=Cost())

    chat = FakeLLM(
        script=[json.dumps({"calls": [{"tool": "search", "args": {"query": "anything"}}]})]
    )
    connection = open_readonly(config.workspace.db_path)
    try:
        answer = run_ask(
            "anything",
            config=config,
            connection=connection,
            handler=empty,
            chat=chat,
            max_rounds=1,
        )
    finally:
        connection.close()
    assert kb.stats().records > 0
    assert answer.insufficient_evidence is True
    assert answer.text == ""
    assert answer.citations == []


def test_fr_053_sdk_ask_with_fake_provider(tmp_path: Path) -> None:
    synced_workspace(tmp_path)
    kb = Lodestone.open(tmp_path, offline=True)
    answer = kb.ask("Why does restore stall?", max_rounds=1, provider="fake")
    assert answer.rounds == 1
    if not answer.insufficient_evidence:
        assert answer.citations
        assert all(label.startswith("E") for label in answer.citations)


def test_fr_055_adversarial_sufficiency_terminates(tmp_path: Path) -> None:
    chat = NeverSufficient()
    answer = _run(tmp_path, "Why does restore stall after manifest load?", chat, max_rounds=3)
    assert answer.rounds <= 3
    assert len(answer.logged_rounds) <= 3
    assert answer.logged_rounds
    for round_calls in answer.logged_rounds:
        assert round_calls
        assert all(
            call["tool"] in {"search", "grep", "who_knows", "recent"} for call in round_calls
        )
