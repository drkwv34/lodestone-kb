# SPDX-License-Identifier: Apache-2.0
"""Validated TOML registry updates; unrelated configuration values are preserved."""

from __future__ import annotations

import json
import os
import tempfile
import tomllib
from datetime import date, datetime
from pathlib import Path

from lodestone.config import Config


def value(item: object) -> str:
    if isinstance(item, bool):
        return "true" if item else "false"
    if isinstance(item, (date, datetime)):
        return item.isoformat()
    if isinstance(item, (str, int, float)):
        return json.dumps(item, ensure_ascii=False)
    if isinstance(item, list):
        return "[" + ", ".join(value(part) for part in item) + "]"
    if isinstance(item, dict):
        return (
            "{ "
            + ", ".join(
                f"{json.dumps(str(key))} = {value(part)}"
                for key, part in item.items()
                if part is not None
            )
            + " }"
        )
    raise ValueError("unsupported TOML value")


def registry_text(path: Path, config: Config) -> str:
    """Re-emit TOML values, replacing only source/project arrays (comments are not retained)."""
    config.validate_registry()
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    data["sources"] = [
        source.model_dump(mode="json", exclude_none=True) for source in config.sources
    ]
    data["projects"] = [project.model_dump(mode="json") for project in config.projects]
    result = (
        "# SPDX-License-Identifier: Apache-2.0\n"
        + "\n".join(f"{json.dumps(key)} = {value(item)}" for key, item in data.items())
        + "\n"
    )
    Config.model_validate(tomllib.loads(result)).validate_registry()
    return result


def replace_config(path: Path, text: str) -> None:
    """Use a private sibling file and atomic rename, including on Windows."""
    descriptor, temporary = tempfile.mkstemp(prefix=".lodestone-", suffix=".toml", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
