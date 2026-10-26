# SPDX-License-Identifier: Apache-2.0
"""Locate versioned JSON schemas shipped in the repo or the installed wheel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def schema_path(name: str) -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "schemas" / name,
        here.parents[1] / "schemas" / name,
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(name)


def load_schema(name: str) -> dict[str, Any]:
    payload: object = json.loads(schema_path(name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be an object")
    return payload
