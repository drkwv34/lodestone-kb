# SPDX-License-Identifier: Apache-2.0
"""Chat providers used by distillation; no storage imports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lodestone.config import Config
from lodestone.providers.chat import ChatResult, OpenAIChat, ProviderError, extract_json
from lodestone.providers.fake import FakeLLM

LogFn = Callable[[str, ChatResult], None]


class Chat(Protocol):
    model: str
    log: LogFn | None

    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool = False, op: str = "chat"
    ) -> ChatResult: ...


def make_chat(config: Config, provider: str | None = None) -> Chat | None:
    if provider is None:
        return None
    if provider == "fake":
        return FakeLLM()
    if provider == "config":
        if config.llm is None:
            raise ValueError("llm is not configured")
        return OpenAIChat.from_config(config.llm)
    raise ValueError(f"unknown provider: {provider}")


__all__ = [
    "Chat",
    "ChatResult",
    "FakeLLM",
    "OpenAIChat",
    "ProviderError",
    "extract_json",
    "make_chat",
]
