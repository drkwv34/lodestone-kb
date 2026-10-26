# SPDX-License-Identifier: Apache-2.0
"""Deterministic FakeLLM: scripted replies plus rule-based cards, rerank and plans."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable

from lodestone.providers.chat import ChatResult, estimate_tokens
from lodestone.tokenize import tokenize

RECORD = re.compile(r'<record kind="[^"]*" title="([^"]*)">\n?(.*?)</record>', re.S)
IDENTIFIER = re.compile(r"[A-Za-z]+[0-9_]|[A-Za-z]+(?:[A-Z][a-z0-9]+)+")


class FakeLLM:
    """Network-free chat stand-in for tests and `--provider fake`."""

    def __init__(
        self,
        script: list[str] | None = None,
        *,
        model: str = "fake",
        log: Callable[[str, ChatResult], None] | None = None,
    ) -> None:
        self.script = list(script or [])
        self.model = model
        self.log = log
        self.calls: list[list[dict[str, str]]] = []
        self._lock = threading.Lock()

    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool = False, op: str = "chat"
    ) -> ChatResult:
        started = time.monotonic()
        with self._lock:
            self.calls.append(messages)
            text = self.script.pop(0) if self.script else self._rule(messages, json_mode=json_mode)
        result = ChatResult(
            text=text,
            model=self.model,
            in_tokens=estimate_tokens(json.dumps(messages)),
            out_tokens=estimate_tokens(text),
            latency_ms=int((time.monotonic() - started) * 1000),
            ok=True,
        )
        if self.log is not None:
            self.log(op, result)
        return result

    def _rule(self, messages: list[dict[str, str]], *, json_mode: bool) -> str:
        blob = "\n".join(message.get("content", "") for message in messages)
        lower = blob.lower()
        if "context prefix" in lower or "self-contained" in lower:
            title = RECORD.search(blob)
            label = title.group(1) if title else "record"
            return (
                f"XYZZY_CONTEXT_TOKEN This chunk belongs to {label} "
                "and should be read with that surrounding context."
            )
        if "retrieval card" in lower or "<record" in lower or op_is_card(lower):
            return card_json(blob)
        if "rerank" in lower:
            return json.dumps(rerank_by_overlap(blob))
        if "planner" in lower or "tool calls" in lower:
            return json.dumps(default_plan(blob))
        if "sufficient" in lower or "need:<query>" in lower:
            return "SUFFICIENT"
        if "<evidence" in lower or "untrusted" in lower:
            ids = re.findall(r'id="(E\d+)"', blob)
            if not ids:
                return "No supporting evidence is available."
            cites = " ".join(f"[{label}]" for label in ids[:5])
            return f"The retrieved records support this answer {cites}."
        return "{}" if json_mode else blob

    def close(self) -> None:
        return


def op_is_card(lower: str) -> bool:
    return "question" in lower and "entities" in lower and "code_refs" in lower


def card_json(blob: str) -> str:
    match = RECORD.search(blob)
    title = match.group(1) if match else ""
    text = match.group(2) if match else blob
    line = next((part.strip() for part in text.splitlines() if part.strip()), title or "unknown")
    question = (title or line)[:200]
    summary = " ".join(text.split())[:500]
    return json.dumps(
        {
            "question": question,
            "summary": summary,
            "resolution": "",
            "entities": [],
            "code_refs": [],
        }
    )


def rerank_by_overlap(blob: str) -> list[dict[str, object]]:
    query = ""
    for line in blob.splitlines():
        if line.lower().startswith("query:"):
            query = line.split(":", 1)[1].strip()
            break
    qtokens = set(tokenize(query))
    ranked: list[tuple[str, int]] = []
    for match in re.finditer(r"id[=:]?\s*[\"']?(\w+)[\"']?\s+(.*)", blob):
        ident, snippet = match.group(1), match.group(2)
        overlap = len(qtokens & set(tokenize(snippet)))
        ranked.append((ident, min(10, overlap)))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [{"id": ident, "score": score} for ident, score in ranked] or [{"id": "0", "score": 0}]


def default_plan(blob: str) -> dict[str, object]:
    question = blob.strip().splitlines()[-1] if blob.strip() else ""
    calls: list[dict[str, object]] = [{"tool": "search", "args": {"query": question}}]
    if IDENTIFIER.search(question):
        calls.append({"tool": "grep", "args": {"pattern": question, "regex": False}})
    return {"calls": calls}
