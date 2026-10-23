# SPDX-License-Identifier: Apache-2.0
"""Shared workspace bootstrap for MCP and ask tests."""

from __future__ import annotations

import shutil
from pathlib import Path

from lodestone.config import load_config
from lodestone.workspace import initialise, sync_workspace

CORPUS = Path(__file__).parent / "fixtures/corpus"


def synced_workspace(tmp_path: Path, extra: dict[str, str] | None = None) -> Path:
    shutil.copytree(CORPUS, tmp_path / "corpus")
    if extra:
        docs = tmp_path / "inject"
        docs.mkdir()
        for name, text in extra.items():
            (docs / name).write_text(text, encoding="utf-8")
    initialise(tmp_path)
    config_path = tmp_path / "lodestone.toml"
    sources = 'sources = ["wiki"]' if not extra else 'sources = ["wiki", "inject"]'
    text = config_path.read_text(encoding="utf-8").replace("sources = []", sources)
    extra_source = ""
    if extra:
        extra_source = '\n[[sources]]\nname="inject"\nkind="files"\npath="inject"\n'
    config_path.write_text(
        text
        + '\n[[sources]]\nname="wiki"\nkind="files"\npath="corpus"\nexclude=["drafts/**"]\n'
        + extra_source,
        encoding="utf-8",
    )
    config = load_config(config_path)
    sync_workspace(config, offline=True)
    return config_path
