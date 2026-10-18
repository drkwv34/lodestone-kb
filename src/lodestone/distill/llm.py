# SPDX-License-Identifier: Apache-2.0
"""LLM card distillation with two validation retries then heuristic fallback."""

from __future__ import annotations

import json
import sqlite3

from pydantic import ValidationError

from lodestone.distill.heuristic import heuristic_card
from lodestone.distill.render import render_prompt, with_provenance
from lodestone.distill.schema import Card
from lodestone.providers import Chat, ProviderError
from lodestone.providers.chat import extract_json

MAX_ATTEMPTS = 3


def llm_card(
    title: str,
    text: str,
    *,
    kind: str,
    chat: Chat,
    max_input_chars: int,
    connection: sqlite3.Connection | None = None,
    messages: list[tuple[str, str]] | None = None,
    prompt_kind: str | None = None,
) -> tuple[Card, str]:
    prompt = render_prompt(prompt_kind or kind, title, text, max_input_chars)
    conversation: list[dict[str, str]] = [
        {"role": "system", "content": "Return a retrieval card as valid JSON only."},
        {"role": "user", "content": prompt},
    ]
    last_error = "invalid JSON"
    for _attempt in range(MAX_ATTEMPTS):
        try:
            result = chat.complete(conversation, json_mode=True, op="card")
            payload = json.loads(extract_json(result.text))
            if not isinstance(payload, dict):
                raise ValueError("JSON root must be an object")
            card = Card.model_validate(payload)
            ids = [item[0] for item in messages] if messages else None
            return with_provenance(card, text, ids), "llm"
        except (ValueError, ValidationError, json.JSONDecodeError, ProviderError) as exc:
            last_error = str(exc)
            conversation = [
                *conversation,
                {
                    "role": "user",
                    "content": f"Invalid JSON: {last_error}. Return a valid card object only.",
                },
            ]
    return heuristic_card(
        title, text, messages=messages, connection=connection, kind=kind
    ), "heuristic"
