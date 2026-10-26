# SPDX-License-Identifier: Apache-2.0
"""Structured logging with JSON output, timing, and secret scrubbing."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

LogRecordFactory = Callable[..., logging.LogRecord]

SECRET_ASSIGN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|authorization|bearer)([\"']?\s*[:=]\s*)([^\s\"']+)"
)
KEYLIKE = re.compile(r"(?i)\b(sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{8,}|Bearer\s+\S+)")
_CONFIGURED = False


def scrub(value: object) -> object:
    """Redact secret assignments and key-shaped tokens from log payloads."""
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if re.search(r"key|token|secret|password", str(key), re.I)
                else scrub(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        text = SECRET_ASSIGN.sub(r"\1\2[REDACTED]", value)
        return KEYLIKE.sub("[REDACTED]", text)
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "op": getattr(record, "op", None) or record.name,
            "msg": scrub(record.getMessage()),
        }
        duration = getattr(record, "duration_ms", None)
        if duration is not None:
            payload["duration_ms"] = duration
        ids = getattr(record, "ids", None)
        if ids is not None:
            payload["ids"] = ids
        return json.dumps(payload, default=str)


def _factory(old: LogRecordFactory) -> LogRecordFactory:
    def make(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old(*args, **kwargs)
        if isinstance(record.msg, str):
            record.msg = scrub(record.msg)
        if record.args:
            record.args = tuple(scrub(arg) for arg in record.args)
        return record

    return make


def configure_logging() -> None:
    """Install JSON or text logging from LODESTONE_LOG. Safe to call repeatedly."""
    global _CONFIGURED
    root = logging.getLogger()
    level_name = os.environ.get("LODESTONE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    mode = os.environ.get("LODESTONE_LOG", "").strip().lower()
    handler = logging.StreamHandler()
    formatter: logging.Formatter = (
        JsonFormatter() if mode == "json" else logging.Formatter("%(levelname)s %(message)s")
    )
    handler.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    if not _CONFIGURED:
        logging.setLogRecordFactory(_factory(logging.getLogRecordFactory()))
        _CONFIGURED = True


@contextmanager
def timed(op: str, *, ids: list[int] | None = None) -> Iterator[None]:
    log = logging.getLogger("lodestone")
    started = time.monotonic()
    try:
        yield
    finally:
        duration = int((time.monotonic() - started) * 1000)
        log.info(
            "op complete",
            extra={"op": op, "duration_ms": duration, "ids": ids or []},
        )
