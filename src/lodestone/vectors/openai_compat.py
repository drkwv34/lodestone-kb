# SPDX-License-Identifier: Apache-2.0
"""OpenAI-compatible embeddings client with the chat retry policy."""

from __future__ import annotations

import json
import math
import random
import time
from collections.abc import Callable
from typing import Self

import httpx

from lodestone.config import Embed
from lodestone.providers.chat import (
    BACKOFF_BASE,
    RETRY_STATUSES,
    ChatResult,
    ProviderError,
    estimate_tokens,
)
from lodestone.providers.offline import is_offline, reject_remote


class OpenAICompatEmbedder:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dim: int = 768,
        api_key: str = "",
        timeout_s: float = 60,
        max_retries: int = 4,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        backoff_base: float = BACKOFF_BASE,
        transport: httpx.BaseTransport | None = None,
        log: Callable[[str, ChatResult], None] | None = None,
    ) -> None:
        reject_remote("embedder")
        self.model = model
        self.dim = dim
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.max_retries = max_retries
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
    def from_config(cls, embed: Embed) -> Self:
        secret = embed.secret("embed")
        return cls(
            base_url=str(embed.base_url),
            model=embed.model,
            dim=embed.dim,
            api_key=secret.get_secret_value() if secret else "",
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        reject_remote("embedder")
        if not texts:
            return []
        payload: dict[str, object] = {"model": self.model, "input": texts}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                vectors = self._attempt(payload, started, texts)
                return vectors
            except (httpx.TimeoutException, httpx.TransportError, ProviderError) as exc:
                last_error = exc
                failed = ChatResult(
                    text=str(exc),
                    model=self.model,
                    in_tokens=estimate_tokens("\n".join(texts)),
                    out_tokens=0,
                    latency_ms=int((time.monotonic() - started) * 1000),
                    ok=False,
                )
                self._emit(failed)
                if attempt >= self.max_retries or not self._retryable(exc):
                    raise ProviderError(str(exc)) from exc
                delay = self.backoff_base * (2**attempt)
                delay *= 1 + self.rng.uniform(-0.25, 0.25)
                self.sleep(max(0.0, delay))
        raise ProviderError(str(last_error) if last_error else "embedder failed")

    def _attempt(
        self, payload: dict[str, object], started: float, texts: list[str]
    ) -> list[list[float]]:
        if is_offline():
            reject_remote("embedder")
        response = self._client.post("/embeddings", json=payload)
        latency = int((time.monotonic() - started) * 1000)
        if response.status_code in RETRY_STATUSES:
            raise ProviderError(f"HTTP {response.status_code}")
        if response.status_code != 200:
            raise ProviderError(f"HTTP {response.status_code}") from None
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError("truncated or invalid JSON body") from exc
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or len(data) != len(texts):
            raise ProviderError("missing embeddings")
        ordered = sorted(
            (item for item in data if isinstance(item, dict)),
            key=lambda item: int(item.get("index") or 0),
        )
        vectors: list[list[float]] = []
        for item in ordered:
            raw = item.get("embedding")
            if not isinstance(raw, list) or not raw:
                raise ProviderError("missing embedding vector")
            vectors.append([float(value) for value in raw])
        usage = body.get("usage") if isinstance(body, dict) else None
        prompt = 0
        if isinstance(usage, dict):
            prompt = int(usage.get("prompt_tokens") or 0)
        model = str(body.get("model") or self.model) if isinstance(body, dict) else self.model
        self._emit(
            ChatResult(
                text="",
                model=model,
                in_tokens=prompt or estimate_tokens("\n".join(texts)),
                out_tokens=0,
                latency_ms=latency,
                ok=True,
            )
        )
        if vectors:
            self.dim = len(vectors[0])
        return [_l2(vector) for vector in vectors]

    def _retryable(self, exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
            return True
        text = str(exc)
        return text.startswith("HTTP 429") or text.startswith("HTTP 5") or "JSON" in text

    def _emit(self, result: ChatResult) -> None:
        if self.log is not None:
            self.log("embed", result)

    def close(self) -> None:
        self._client.close()


def _l2(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0.0:
        return vector
    return [item / norm for item in vector]
