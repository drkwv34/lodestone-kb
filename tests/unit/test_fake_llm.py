# SPDX-License-Identifier: Apache-2.0
import json
import socket

import pytest

from lodestone.config import LLM, Config
from lodestone.providers import make_chat
from lodestone.providers.chat import OpenAIChat
from lodestone.providers.fake import FakeLLM, default_plan, rerank_by_overlap


def test_fr_063_scripted_and_rule_based_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("FakeLLM must not open sockets")

    monkeypatch.setattr(socket, "socket", blocked)
    scripted = FakeLLM(script=["alpha", "beta"])
    assert scripted.complete([{"role": "user", "content": "one"}]).text == "alpha"
    assert scripted.complete([{"role": "user", "content": "two"}]).text == "beta"
    rule = FakeLLM()
    card = json.loads(
        rule.complete(
            [
                {
                    "role": "user",
                    "content": (
                        'Return a retrieval card.\n<record kind="doc" title="Latch">text</record>'
                    ),
                }
            ],
            json_mode=True,
            op="card",
        ).text
    )
    assert card["question"] == "Latch"
    assert card["summary"] == "text"
    plan = default_plan("Find ERR_MANIFEST_TIMEOUT")
    assert plan["calls"][0]["tool"] == "search"
    assert any(call["tool"] == "grep" for call in plan["calls"])  # type: ignore[index]
    ranked = rerank_by_overlap("query: apple\nid=1 apple pie\nid=2 orange")
    assert ranked[0]["id"] == "1"
    rule.close()


def test_fr_063_make_chat_provider_selection() -> None:
    config = Config()
    assert make_chat(config) is None
    fake = make_chat(config, "fake")
    assert isinstance(fake, FakeLLM)
    with pytest.raises(ValueError, match="llm is not configured"):
        make_chat(config, "config")
    with pytest.raises(ValueError, match="unknown provider"):
        make_chat(config, "nope")
    remote = make_chat(Config(llm=LLM()), "config")
    assert isinstance(remote, OpenAIChat)
    remote.close()
