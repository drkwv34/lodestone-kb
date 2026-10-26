# SPDX-License-Identifier: Apache-2.0
"""JSONL resume cache keyed by strategy, config hash, corpus hash, and qid."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def cache_key(strategy: str, config_hash: str, corpus_hash: str, qid: str) -> str:
    return f"{strategy}\0{config_hash}\0{corpus_hash}\0{qid}"


@dataclass
class CachedResult:
    strategy: str
    config_hash: str
    corpus_hash: str
    qid: str
    retrieved: list[str]
    answer: str
    in_tokens: int
    out_tokens: int
    latency_ms: float
    scores: dict[str, float]

    def dump(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "config_hash": self.config_hash,
            "corpus_hash": self.corpus_hash,
            "qid": self.qid,
            "retrieved": list(self.retrieved),
            "answer": self.answer,
            "in_tokens": self.in_tokens,
            "out_tokens": self.out_tokens,
            "latency_ms": self.latency_ms,
            "scores": dict(self.scores),
        }


class ResultCache:
    """Append-only JSONL cache; last write for a key wins."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._entries: dict[str, CachedResult] = {}
        if path.is_file():
            self._load()

    def _load(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                continue
            item = CachedResult(
                strategy=str(payload.get("strategy") or ""),
                config_hash=str(payload.get("config_hash") or ""),
                corpus_hash=str(payload.get("corpus_hash") or ""),
                qid=str(payload.get("qid") or ""),
                retrieved=[str(ident) for ident in payload.get("retrieved") or []],
                answer=str(payload.get("answer") or ""),
                in_tokens=int(payload.get("in_tokens") or 0),
                out_tokens=int(payload.get("out_tokens") or 0),
                latency_ms=float(payload.get("latency_ms") or 0.0),
                scores={
                    str(key): float(value) for key, value in (payload.get("scores") or {}).items()
                },
            )
            self._entries[
                cache_key(item.strategy, item.config_hash, item.corpus_hash, item.qid)
            ] = item

    def get(
        self, strategy: str, config_hash: str, corpus_hash: str, qid: str
    ) -> CachedResult | None:
        return self._entries.get(cache_key(strategy, config_hash, corpus_hash, qid))

    def put(self, item: CachedResult) -> None:
        self._entries[cache_key(item.strategy, item.config_hash, item.corpus_hash, item.qid)] = item
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(item.dump(), ensure_ascii=True, separators=(",", ":")) + "\n")
