# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

from lodestone.bench.runner import run_bench
from lodestone.bench.synth import generate
from lodestone.providers.chat import ChatResult
from lodestone.providers.fake import FakeLLM


class CountingChat:
    model = "fake"
    log = None

    def __init__(self) -> None:
        self.inner = FakeLLM()
        self.calls = 0

    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool = False, op: str = "chat"
    ) -> ChatResult:
        self.calls += 1
        return self.inner.complete(messages, json_mode=json_mode, op=op)


def test_fr_078_resume_zero_duplicate_llm_calls(tmp_path: Path) -> None:
    corpus = generate(tmp_path / "corpus", seed=4, threads=2)
    chat = CountingChat()
    out = tmp_path / "run"
    first = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=out,
        strategies="full-context",
        k=5,
        context_budget=1_000_000,
        chat=chat,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    assert first.strategies[0].status == "ok"
    assert chat.calls > 0
    baseline = chat.calls
    second = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=out,
        strategies="full-context",
        k=5,
        context_budget=1_000_000,
        chat=chat,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    assert chat.calls == baseline
    assert all(row.cached for row in second.strategies[0].questions)
