# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from lodestone.config import LLM, Config, Source
from lodestone.ingest.pipeline import sync
from lodestone.providers.chat import OpenAIChat
from tests.http_support import Scripted, chat_body, serve

CARD = json.dumps(
    {
        "question": "Why?",
        "summary": "Because the token is unique.",
        "resolution": "",
        "entities": [],
        "code_refs": [],
    }
)


def test_fr_018_ingest_concurrency_cap_under_429_500(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    for index in range(4):
        (root / f"n{index}.md").write_text(
            f"# Note {index}\nunique_{index} token\n", encoding="utf-8"
        )
    replies = [
        Scripted(status=429, body=b'{"error":"rate"}'),
        Scripted(status=500, body=b"err"),
        *[Scripted(body=chat_body(CARD), delay=0.05) for _ in range(12)],
    ]
    with serve(replies) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}/v1"
        chat = OpenAIChat(
            base_url=url,
            model="test",
            timeout_s=2,
            max_retries=3,
            sleep=lambda _delay: None,
            backoff_base=0.0,
        )
        config = Config(
            sources=[Source(name="docs", kind="files", path=root)],
            llm=LLM(base_url=url, max_concurrency=2, max_retries=3),  # type: ignore[arg-type]
        )
        report = sync(database, config, chat=chat)
        chat.close()
    assert report.processed >= 4
    assert report.max_concurrency <= 2
    assert report.max_concurrency >= 1
    assert report.cards_llm + report.cards_heuristic >= 1
