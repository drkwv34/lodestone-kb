# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from lodestone.ask.pipeline import run_ask
from lodestone.config import Config, Retrieval
from lodestone.distill.apply import generate_card
from lodestone.fusion.pipeline import fused_search
from lodestone.lanes.scope import Scope
from lodestone.lanes.vec import search as vec_search
from lodestone.providers.chat import ChatResult, ProviderError
from lodestone.providers.fake import FakeLLM


class BoomLLM(FakeLLM):
    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool = False, op: str = "chat"
    ) -> ChatResult:
        blob = "\n".join(message.get("content", "") for message in messages).lower()
        if op in {"synthesis", "rerank", "card"} or "<evidence" in blob or "reranker" in blob:
            raise ProviderError("injected provider failure")
        if "retrieval card" in blob or "<record" in blob:
            raise ProviderError("injected provider failure")
        return super().complete(messages, json_mode=json_mode, op=op)


def test_nfr_007_provider_failures_degrade(database, record_factory) -> None:
    card, used = generate_card("alpha", "alpha unique token", "doc", Config(), BoomLLM(), None)
    assert used == "heuristic"
    assert card.summary
    record_factory("alpha unique token for degrade", title="alpha", ext_id="a.md")
    fused = fused_search(
        database,
        Config(retrieval=Retrieval(lanes=["fts_raw"])),
        "alpha",
        scope=Scope(),
        rerank=True,
        chat=BoomLLM(),
    )
    assert fused.hits
    assert any("rerank failed" in notice or "fused order" in notice for notice in fused.notices)
    skipped = vec_search(database, "alpha", lane="vec_card", embedder=None, limit=5)
    assert skipped.hits == []
    assert any("skipped" in notice for notice in skipped.notices)

    def handler(tool: str, args: dict[str, object]) -> object:
        del tool, args
        return type("R", (), {"hits": fused.hits, "notices": [], "packets": []})()

    answer = run_ask(
        "alpha?",
        config=Config(),
        connection=database,
        handler=handler,
        chat=BoomLLM(),
        max_rounds=1,
    )
    assert "Provider error" in answer.text
    assert "Partial evidence" in answer.text
    assert answer.citations or "E" in answer.text
