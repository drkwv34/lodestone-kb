# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from lodestone.ask.pipeline import run_ask
from lodestone.config import load_config
from lodestone.providers.fake import FakeLLM, default_plan
from lodestone.sdk import Lodestone
from lodestone.storage.db import open_readonly
from tests.helpers import synced_workspace

INJECTION = Path(__file__).parents[1] / "fixtures/injection"
ALLOWED = {"search", "grep", "who_knows", "recent"}


def test_fr_056_injection_payloads_do_not_alter_tools() -> None:
    payloads = sorted(INJECTION.glob("*.txt"))
    assert len(payloads) == 10
    question = "What is ERR_MANIFEST_TIMEOUT?"
    expected = default_plan(question)["calls"]
    expected_tools = [call["tool"] for call in expected]  # type: ignore[index]
    for path in payloads:
        text = path.read_text(encoding="utf-8")
        with TemporaryDirectory() as raw:
            config_path = synced_workspace(Path(raw), extra={path.name: text})
            config = load_config(config_path)
            kb = Lodestone(config, offline=True)
            connection = open_readonly(config.workspace.db_path)
            try:
                answer = run_ask(
                    question,
                    config=config,
                    connection=connection,
                    handler=kb._dispatch,
                    chat=FakeLLM(),
                    max_rounds=1,
                )
            finally:
                connection.close()
            planned_tools = [call["tool"] for call in answer.plan]
            assert planned_tools == expected_tools, path.name
            assert set(planned_tools) <= ALLOWED
            assert "drop_table" not in planned_tools
            assert "[E99]" not in answer.text
            assert isinstance(answer.insufficient_evidence, bool)
            for label in answer.citations:
                assert label.startswith("E")
