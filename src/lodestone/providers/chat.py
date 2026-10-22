# SPDX-License-Identifier: Apache-2.0
"""OpenAI-compatible chat client with retry, backoff and tolerant JSON extraction."""

from __future__ import annotations

import json
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

import httpx

from lodestone.config import LLM
from lodestone.providers.offline import reject_remote

RETRY_STATUSES = {429, 500, 502, 503, 504}
BACKOFF_BASE = 0.5
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


class ProviderError(RuntimeError):
    """Remote chat provider failed after retries."""


@dataclass(frozen=True)
class ChatResult:
    text: str
    model: str
    in_tokens: int
    out_tokens: int
    latency_ms: int
    ok: bool


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4 if text else 0


def extract_json(text: str) -> str:
    cleaned = FENCE.sub("", text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("response did not contain a JSON object")
    payload = cleaned[start : end + 1]
    json.loads(payload)
    return payload


def parse_json(text: str) -> object:
    cleaned = FENCE.sub("", text.strip())
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char in "{[":
            try:
                value, _end = decoder.raw_decode(cleaned[index:])
            except json.JSONDecodeError:
                continue
            return value
    raise ValueError("response did not contain JSON")


class OpenAIChat:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_s: float = 60,
        max_retries: int = 4,
        json_mode: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        backoff_base: float = BACKOFF_BASE,
        transport: httpx.BaseTransport | None = None,
        log: Callable[[str, ChatResult], None] | None = None,
    ) -> None:
        reject_remote("provider")
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.json_mode = json_mode
        self.sleep = sleep
        self.rng = rng or random.Random()  # noqa: S311 - jitter, not cryptography
        self.backoff_base = backoff_base
        self.log = log
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout_s,
            transport=transport,
        )

    @classmethod
    def from_config(cls, llm: LLM) -> Self:
        secret = llm.secret("llm")
        return cls(
            base_url=str(llm.base_url),
            model=llm.model,
            api_key=secret.get_secret_value() if secret else "",
            timeout_s=llm.timeout_s,
            max_retries=llm.max_retries,
            json_mode=llm.json_mode,
        )

    def complete(
        self, messages: list[dict[str, str]], *, json_mode: bool | None = None, op: str = "chat"
    ) -> ChatResult:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }
        if json_mode if json_mode is not None else self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        reject_remote("provider")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                result = self._attempt(payload, started)
                self._emit(op, result)
                if not result.ok:
                    raise ProviderError(result.text or "provider returned an unusable body")
                return result
            except (httpx.TimeoutException, httpx.TransportError, ProviderError) as exc:
                last_error = exc
                failed = ChatResult(
                    text=str(exc),
                    model=self.model,
                    in_tokens=estimate_tokens(json.dumps(messages)),
                    out_tokens=0,
                    latency_ms=int((time.monotonic() - started) * 1000),
                    ok=False,
                )
                self._emit(op, failed)
                if attempt >= self.max_retries or not self._retryable(exc):
                    raise ProviderError(str(exc)) from exc
                delay = self.backoff_base * (2**attempt)
                delay *= 1 + self.rng.uniform(-0.25, 0.25)
                self.sleep(max(0.0, delay))
        raise ProviderError(str(last_error) if last_error else "provider failed")

    def _attempt(self, payload: dict[str, object], started: float) -> ChatResult:
        response = self._client.post("/chat/completions", json=payload)
        latency = int((time.monotonic() - started) * 1000)
        if response.status_code in RETRY_STATUSES:
            raise ProviderError(f"HTTP {response.status_code}")
        if response.status_code != 200:
            raise ProviderError(f"HTTP {response.status_code}") from None
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError("truncated or invalid JSON body") from exc
        choices = body.get("choices") if isinstance(body, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ProviderError("missing choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ProviderError("missing message content")
        usage = body.get("usage") if isinstance(body, dict) else None
        prompt = completion = 0
        if isinstance(usage, dict):
            prompt = int(usage.get("prompt_tokens") or 0)
            completion = int(usage.get("completion_tokens") or 0)
        model = str(body.get("model") or self.model) if isinstance(body, dict) else self.model
        return ChatResult(
            text=content,
            model=model,
            in_tokens=prompt or estimate_tokens(json.dumps(payload.get("messages"))),
            out_tokens=completion or estimate_tokens(content),
            latency_ms=latency,
            ok=True,
        )

    def _retryable(self, exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
            return True
        text = str(exc)
        return text.startswith("HTTP 429") or text.startswith("HTTP 5") or "JSON" in text

    def _emit(self, op: str, result: ChatResult) -> None:
        if self.log is not None:
            self.log(op, result)

    def close(self) -> None:
        self._client.close()
