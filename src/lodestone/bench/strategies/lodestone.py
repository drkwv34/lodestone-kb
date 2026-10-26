# SPDX-License-Identifier: Apache-2.0
"""lodestone-lexical: heuristic cards plus FTS lanes, no embeddings."""

from __future__ import annotations

import json
import time
from pathlib import Path

from lodestone.bench.strategies.base import IndexStats
from lodestone.config import load_config
from lodestone.workspace import initialise, search_result, sync_workspace


class LodestoneLexical:
    name = "lodestone-lexical"
    skipped: str | None = None

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.config_path = directory / "lodestone.toml"

    def index(self, corpus: Path) -> IndexStats:
        started = time.perf_counter()
        self.directory.mkdir(parents=True, exist_ok=True)
        initialise(self.directory)
        docs = corpus.resolve()
        threads = (corpus / "threads.jsonl").resolve()
        text = (
            "# SPDX-License-Identifier: Apache-2.0\n"
            "schema_version = 1\n"
            "offline = true\n"
            "[workspace]\n"
            'db_path = ".lodestone/index.db"\n'
            'default_project = "default"\n'
            "[retrieval]\n"
            'lanes = ["fts_raw", "fts_card", "fts_rare"]\n'
            "candidate_pool = 50\n"
            "max_per_source = 50\n"
            "[embed]\n"
            'provider = "none"\n'
            "[[projects]]\n"
            'name = "default"\n'
            'sources = ["docs", "threads"]\n'
            "[[sources]]\n"
            'name = "docs"\n'
            'kind = "files"\n'
            f"path = {json.dumps(docs.as_posix())}\n"
            'include = ["docs/**", "code/**"]\n'
            "[[sources]]\n"
            'name = "threads"\n'
            'kind = "threads"\n'
            f"path = {json.dumps(threads.as_posix())}\n"
        )
        self.config_path.write_text(text, encoding="utf-8", newline="\n")
        config = load_config(self.config_path)
        sync_workspace(config, offline=True)
        db_path = config.workspace.db_path
        return IndexStats(
            seconds=time.perf_counter() - started,
            bytes=db_path.stat().st_size if db_path.exists() else 0,
        )

    def retrieve(self, question: str, k: int) -> list[str]:
        config = load_config(self.config_path)
        result = search_result(config, question, limit=k, offline=True, decay=True, rerank=False)
        return [hit.ext_id for hit in result.hits]

    def close(self) -> None:
        return None
