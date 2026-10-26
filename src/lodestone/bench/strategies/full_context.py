# SPDX-License-Identifier: Apache-2.0
"""full-context: stuff the corpus in one prompt, or skip when over budget."""

from __future__ import annotations

import time
from pathlib import Path

from lodestone.bench.metrics import collapse_parents
from lodestone.bench.strategies.base import DEFAULT_CONTEXT_BUDGET, IndexStats
from lodestone.bench.strategies.chunks import load_corpus
from lodestone.providers import Chat, FakeLLM
from lodestone.tokenize import tokenize


class FullContext:
    name = "full-context"
    skipped: str | None

    def __init__(
        self,
        directory: Path,
        *,
        budget: int = DEFAULT_CONTEXT_BUDGET,
        chat: Chat | None = None,
    ) -> None:
        if budget < 1:
            raise ValueError("context budget must be positive")
        self.directory = directory
        self.budget = budget
        self.chat: Chat = chat if chat is not None else FakeLLM()
        self.skipped = None
        self.blob = ""
        self.ids: list[str] = []
        self.last_answer = ""
        self.last_in_tokens = 0
        self.last_out_tokens = 0

    def index(self, corpus: Path) -> IndexStats:
        started = time.perf_counter()
        items = load_corpus(corpus)
        self.ids = collapse_parents([item.ext_id for item in items])
        parts = [f"[{item.ext_id}]\n{item.text}" for item in items]
        self.blob = "\n\n".join(parts)
        tokens = len(tokenize(self.blob)) if self.blob else 0
        if tokens > self.budget:
            self.skipped = "too_large"
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "budget.txt").write_text(str(self.budget), encoding="utf-8")
        return IndexStats(
            seconds=time.perf_counter() - started,
            bytes=len(self.blob.encode("utf-8")),
            in_tokens=tokens,
        )

    def retrieve(self, question: str, k: int) -> list[str]:
        if self.skipped:
            return []
        return self.ids[:k]

    def answer(self, question: str) -> str:
        if self.skipped:
            self.last_answer = ""
            return ""
        result = self.chat.complete(
            [
                {
                    "role": "user",
                    "content": (
                        "Answer the question using only the corpus text.\n"
                        f"Question: {question}\nCorpus:\n{self.blob[:200000]}"
                    ),
                }
            ],
            json_mode=False,
            op="full-context",
        )
        self.last_in_tokens = result.in_tokens
        self.last_out_tokens = result.out_tokens
        self.last_answer = result.text
        return result.text

    def close(self) -> None:
        return None
