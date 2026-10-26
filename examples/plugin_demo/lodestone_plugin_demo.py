# SPDX-License-Identifier: Apache-2.0
"""Demo connector: each *.note file becomes one document (FR-017, <= 60 lines)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lodestone.connectors.files import RawItem, Skip


class NotesConnector:
    name = "notes"

    def __init__(self) -> None:
        self.skipped: list[Skip] = []

    def discover(self, cfg: Any) -> Iterator[RawItem]:
        root = Path(str(cfg.path))
        if not root.is_dir():
            raise ValueError("notes source path must be a directory")
        self.skipped.clear()
        for path in sorted(root.glob("*.note")):
            text = path.read_text(encoding="utf-8")
            yield RawItem(
                ext_id=path.name,
                kind_hint="md",
                title=path.stem,
                text=text,
                metadata={"path": path.name, "plugin": "notes"},
                updated_at=datetime.fromtimestamp(path.stat().st_mtime, UTC),
            )
