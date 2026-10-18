# SPDX-License-Identifier: Apache-2.0
import json
import random

import pytest

from lodestone.providers.chat import OpenAIChat, ProviderError, extract_json
from tests.http_support import Scripted, chat_body, serve

VALID = '{"question":"Why?","summary":"Because.","resolution":"","entities":[],"code_refs":[]}'


def client(url: str, timeout_s: float = 0.2, max_retries: int = 2) -> OpenAIChat:
    return OpenAIChat(
        base_url=url,
        model="test",
        api_key="dummy",
        timeout_s=timeout_s,
        max_retries=max_retries,
        sleep=lambda _delay: None,
        rng=random.Random(0),  # noqa: S311
        backoff_base=0.0,
    )


def test_fr_060_provider_fault_injection() -> None:
    with serve(
        [
            Scripted(body=chat_body("ok-200")),
            Scripted(status=429, body=b'{"error":"rate"}'),
            Scripted(body=chat_body("after-429")),
            Scripted(status=500, body=b"err"),
            Scripted(body=chat_body("after-500")),
            Scripted(body=b'{"choices":['),
            Scripted(body=chat_body("after-truncated")),
            Scripted(status=200, body=chat_body("slow"), delay=0.5),
        ]
    ) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        chat = client(url)
        assert chat.complete([{"role": "user", "content": "hi"}]).text == "ok-200"
        assert json.loads(server.requests[0])["response_format"] == {"type": "json_object"}
        assert chat.complete([{"role": "user", "content": "retry-429"}]).text == "after-429"
        assert chat.complete([{"role": "user", "content": "retry-500"}]).text == "after-500"
        assert chat.complete([{"role": "user", "content": "retry-trunc"}]).text == "after-truncated"
        with pytest.raises(ProviderError):
            client(url, timeout_s=0.05).complete([{"role": "user", "content": "timeout"}])
        chat.close()


def test_fr_060_non_retryable_client_error() -> None:
    with serve([Scripted(status=401, body=b'{"error":"no"}')]) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        chat = client(url, max_retries=3)
        with pytest.raises(ProviderError, match="HTTP 401"):
            chat.complete([{"role": "user", "content": "x"}])
        assert len(server.requests) == 1
        chat.close()


def test_fr_060_extract_json_fences_and_noise() -> None:
    assert json.loads(extract_json("```json\n" + VALID + "\n```"))["question"] == "Why?"
    assert json.loads(extract_json("noise " + VALID + " trailing"))["summary"] == "Because."
    with pytest.raises(ValueError, match="JSON object"):
        extract_json("not an object")
