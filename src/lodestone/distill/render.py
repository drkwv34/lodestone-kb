# SPDX-License-Identifier: Apache-2.0
"""Card rendering, embedding inputs, prompt truncation and provenance spans."""

from __future__ import annotations

from pathlib import Path

from lodestone.distill.schema import Card, CharSpan

PROMPT = Path(__file__).resolve().parents[1] / "prompts" / "card.v1.md"


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit]


def truncate_head_tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    marker = "\n...\n"
    keep = limit - len(marker)
    if keep < 2:
        return text[:limit]
    head = keep // 2
    return text[:head] + marker + text[-(keep - head) :]


def render_prompt(kind: str, title: str, text: str, max_chars: int) -> str:
    body = truncate_head_tail(text, max_chars)
    template = PROMPT.read_text(encoding="utf-8")
    return template.replace("$kind", kind).replace("$title", title).replace("$body", body)


def render_norm(card: Card, fmt: str = "plain") -> str:
    entities = ", ".join(card.entities)
    refs = ", ".join(card.code_refs)
    if fmt == "xml":
        return (
            f"<question>{card.question}</question>\n<summary>{card.summary}</summary>\n"
            f"<resolution>{card.resolution}</resolution>\n<systems>{entities}</systems>\n"
            f"<code>{refs}</code>"
        )
    return f"{card.question}\n{card.summary}\n{card.resolution}\nsystems: {entities}\ncode: {refs}"


def embedding_input(text: str, norm_text: str, source: str) -> list[str]:
    """Select embed strings; raw text is omitted when a card exists and source is card."""
    if source == "raw":
        return [text]
    if source == "both":
        return [norm_text, text] if norm_text else [text]
    return [norm_text] if norm_text else [text]


def with_provenance(card: Card, text: str, message_ids: list[str] | None = None) -> Card:
    spans: list[CharSpan] = []
    for part in (card.question, card.summary, card.resolution):
        if not part:
            continue
        index = text.find(part)
        if index >= 0:
            spans.append(CharSpan(start=index, end=index + len(part)))
    if not spans and text:
        spans.append(CharSpan(start=0, end=min(len(text), 200)))
    ids = list(message_ids or [])
    if not spans and not ids:
        spans.append(CharSpan(start=0, end=0))
    return card.model_copy(update={"source_message_ids": ids, "char_spans": spans})
