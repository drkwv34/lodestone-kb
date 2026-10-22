# SPDX-License-Identifier: Apache-2.0
"""Optional LLM rerank of a fused candidate pool; fallback keeps fused order."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from lodestone.providers import Chat, parse_json
from lodestone.providers.chat import ProviderError
from lodestone.providers.offline import OfflineError

SNIPPET_CHARS = 1200
PROMPT = (
    "You are a reranker. Score each candidate from 0 to 10 for relevance.\n"
    "Return ONLY a JSON array of objects: [{{id, score}}].\n"
    "Query: {query}\n\nCandidates:\n{candidates}\n"
)


@dataclass(frozen=True)
class RerankOutcome:
    order: list[int]
    scores: dict[int, float]
    notice: str | None = None


def _scores(payload: object, known: set[int]) -> dict[int, float]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("malformed rerank payload")
    scores = {ident: 0.0 for ident in known}
    for entry in payload:
        if not isinstance(entry, dict) or "id" not in entry or "score" not in entry:
            raise ValueError("malformed rerank payload")
        try:
            ident = int(entry["id"])
            score = float(entry["score"])
        except (TypeError, ValueError) as exc:
            raise ValueError("malformed rerank payload") from exc
        if ident in scores:
            scores[ident] = max(0.0, min(10.0, score))
    return scores


class LLMReranker:
    """Score fused hits with a chat model; any failure is the caller's fallback."""

    def __init__(self, chat: Chat) -> None:
        self.chat = chat

    def rerank(self, query: str, hits: Sequence[tuple[int, str, float]]) -> list[tuple[int, float]]:
        if not hits:
            return []
        known = [ident for ident, _snippet, _fused in hits]
        lines = [f"id={ident} {snippet[:SNIPPET_CHARS]}" for ident, snippet, _fused in hits]
        result = self.chat.complete(
            [{"role": "user", "content": PROMPT.format(query=query, candidates="\n".join(lines))}],
            json_mode=True,
            op="rerank",
        )
        scores = _scores(parse_json(result.text), set(known))
        fused = {ident: fused_score for ident, _snippet, fused_score in hits}
        ordered = sorted(
            known, key=lambda ident: (scores[ident], fused[ident], -ident), reverse=True
        )
        if sorted(ordered) != sorted(known):
            raise ValueError("rerank is not a permutation")
        return [(ident, scores[ident]) for ident in ordered]


def apply(
    query: str,
    hits: Sequence[tuple[int, str, float]],
    chat: Chat | None,
    *,
    keep: int,
) -> RerankOutcome:
    order = [ident for ident, _snippet, _fused in hits]
    if not order:
        return RerankOutcome([], {})
    if chat is None:
        return RerankOutcome(order, {}, "rerank skipped: no reranker configured")
    try:
        ranked = LLMReranker(chat).rerank(query, hits)
    except (ProviderError, OfflineError, ValueError, TypeError, KeyError, TimeoutError) as extra:
        return RerankOutcome(order, {}, f"rerank failed: {extra}; using fused order")
    scores = {ident: score for ident, score in ranked}
    ordered = [ident for ident, _score in ranked]
    if keep > 0:
        ordered = ordered[:keep]
    return RerankOutcome(ordered, scores)
