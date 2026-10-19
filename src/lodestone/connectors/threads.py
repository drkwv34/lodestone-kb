# SPDX-License-Identifier: Apache-2.0
"""Streaming JSONL thread discovery with line-level skip reporting."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from lodestone.config import Source
from lodestone.connectors.files import Message, RawItem, Skip

LOGGER = logging.getLogger(__name__)


def parse_ts(value: object) -> datetime:
    """Parse ISO-8601 timestamps with Z or numeric offsets; reject naive values."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ts must be an ISO-8601 string")
    raw = value.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("ts must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("naive timestamps are rejected")
    return parsed.astimezone(UTC)


def render_stamp(ts: datetime) -> str:
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ")


def render_message(message: Message) -> str:
    return f"[{render_stamp(message.ts)}] {message.author}: {message.text}"


def render_transcript(messages: tuple[Message, ...] | list[Message]) -> str:
    return "\n".join(render_message(message) for message in messages)


def encode_messages(messages: tuple[Message, ...]) -> str:
    payload = [
        {
            "id": message.id,
            "author": message.author,
            "ts": message.ts.astimezone(UTC).isoformat(),
            "text": message.text,
            "reactions": message.reactions,
        }
        for message in messages
    ]
    return json.dumps(payload, separators=(",", ":"))


def parse_message(raw: object, index: int) -> Message:
    if not isinstance(raw, dict):
        raise ValueError(f"messages[{index}] must be an object")
    ident = raw.get("id")
    author = raw.get("author")
    text = raw.get("text")
    if ident is None or not str(ident):
        raise ValueError(f"messages[{index}] missing id")
    if not isinstance(author, str) or not author:
        raise ValueError(f"messages[{index}] missing author")
    if not isinstance(text, str):
        raise ValueError(f"messages[{index}] text must be a string")
    reactions = raw.get("reactions", 0)
    if isinstance(reactions, bool) or not isinstance(reactions, int) or reactions < 0:
        raise ValueError(f"messages[{index}] reactions must be a non-negative integer")
    return Message(
        id=str(ident),
        author=author,
        ts=parse_ts(raw.get("ts")),
        text=text,
        reactions=reactions,
    )


def parse_thread(raw: object, source: Source) -> RawItem:
    if not isinstance(raw, dict):
        raise ValueError("thread must be a JSON object")
    thread_id = raw.get("thread_id")
    if thread_id is None or not str(thread_id).strip():
        raise ValueError("missing thread_id")
    messages_raw = raw.get("messages")
    if not isinstance(messages_raw, list) or not messages_raw:
        raise ValueError("messages must be a non-empty array")
    messages = tuple(parse_message(item, index) for index, item in enumerate(messages_raw))
    channel = raw.get("channel")
    if channel is None:
        channel = source.channel or ""
    elif not isinstance(channel, str):
        raise ValueError("channel must be a string")
    title = raw.get("title")
    if title is None:
        title = next((message.text.strip() for message in messages if message.text.strip()), "")
        title = title[:200] or str(thread_id)
    elif not isinstance(title, str):
        raise ValueError("title must be a string")
    ident = str(thread_id)
    return RawItem(
        ext_id=ident,
        kind_hint="thread",
        title=title,
        text=render_transcript(messages),
        metadata={
            "channel": channel,
            "uri": f"jsonl://{source.name}#{ident}",
            "messages_json": encode_messages(messages),
        },
        updated_at=max(message.ts for message in messages),
        messages=messages,
    )


class ThreadsConnector:
    def __init__(self) -> None:
        self.skipped: list[Skip] = []

    def skip(self, line: int, reason: str) -> None:
        path = f"line {line}"
        self.skipped.append(Skip(path=path, reason=reason))
        LOGGER.warning("Skipping %s: %s", path, reason)

    def discover(self, cfg: Source) -> Iterator[RawItem]:
        path = cfg.path
        if not path.is_file():
            raise ValueError("threads source path must be a file")
        self.skipped.clear()
        yield from self.read(path, cfg)

    def read(self, path: Path, cfg: Source) -> Iterator[RawItem]:
        with path.open("rb") as stream:
            for number, blob in enumerate(stream, start=1):
                if len(blob) > cfg.max_file_bytes:
                    self.skip(number, "oversize")
                    continue
                try:
                    line = blob.decode("utf-8")
                except UnicodeDecodeError:
                    self.skip(number, "invalid UTF-8")
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                    yield parse_thread(payload, cfg)
                except (json.JSONDecodeError, ValueError, TypeError) as exc:
                    self.skip(number, str(exc))
