# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging

from lodestone.observe import JsonFormatter, scrub, timed


def test_nfr_015_json_logs_without_pii() -> None:
    record = logging.LogRecord(
        name="lodestone",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="api_key=sk-secret-value-12345678 raw record text omitted",
        args=(),
        exc_info=None,
    )
    record.op = "search"
    record.duration_ms = 12
    record.ids = [3]
    line = JsonFormatter().format(record)
    payload = json.loads(line)
    assert payload["op"] == "search"
    assert payload["duration_ms"] == 12
    assert payload["ids"] == [3]
    assert "ts" in payload and "level" in payload
    assert "sk-secret-value" not in line
    assert "[REDACTED]" in payload["msg"]
    with timed("sync", ids=[1]):
        pass


def test_nfr_015_scrub_keys() -> None:
    assert "[REDACTED]" in str(scrub("api_key=sk-secret-value-12345678"))
    assert scrub({"api_key": "x", "path": "ok"}) == {"api_key": "[REDACTED]", "path": "ok"}
