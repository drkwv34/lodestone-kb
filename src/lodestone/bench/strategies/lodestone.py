# SPDX-License-Identifier: Apache-2.0
"""Lodestone workspace strategies: lexical, hybrid, and rerank."""

from __future__ import annotations

import json
import time
from pathlib import Path

from lodestone.bench.strategies.base import IndexStats
from lodestone.config import load_config
from lodestone.providers import Chat
from lodestone.workspace import initialise, search_result, sync_workspace

LEXICAL_LANES = ("fts_raw", "fts_card", "fts_rare")
HYBRID_LANES = (*LEXICAL_LANES, "vec_card", "vec_chunk")


def write_workspace(
    directory: Path,
    corpus: Path,
    *,
    lanes: tuple[str, ...],
    embed: str,
    rerank: bool = False,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    initialise(directory)
    docs = corpus.resolve()
    threads = (corpus / "threads.jsonl").resolve()
    lane_list = ", ".join(json.dumps(lane) for lane in lanes)
    text = (
        "# SPDX-License-Identifier: Apache-2.0\n"
        "schema_version = 1\n"
        "offline = true\n"
        "[workspace]\n"
        'db_path = ".lodestone/index.db"\n'
        'default_project = "default"\n'
        "[retrieval]\n"
        f"lanes = [{lane_list}]\n"
        "candidate_pool = 50\n"
        "max_per_source = 50\n"
        f"rerank = {'true' if rerank else 'false'}\n"
        "[embed]\n"
        f'provider = "{embed}"\n'
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
    path = directory / "lodestone.toml"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


class LodestoneStrategy:
    skipped: str | None = None

    def __init__(
        self,
        directory: Path,
        *,
        name: str,
        lanes: tuple[str, ...],
        embed: str,
        rerank: bool = False,
        provider: str | None = None,
        chat: Chat | None = None,
    ) -> None:
        self.directory = directory
        self.name = name
        self.lanes = lanes
        self.embed = embed
        self.want_rerank = rerank
        self.provider = provider
        self.chat = chat
        self.config_path = directory / "lodestone.toml"
        self.last_in_tokens = 0
        self.last_out_tokens = 0

    def index(self, corpus: Path) -> IndexStats:
        started = time.perf_counter()
        write_workspace(
            self.directory,
            corpus,
            lanes=self.lanes,
            embed=self.embed,
            rerank=self.want_rerank,
        )
        config = load_config(self.config_path)
        sync_workspace(config, offline=True)
        db_path = config.workspace.db_path
        return IndexStats(
            seconds=time.perf_counter() - started,
            bytes=db_path.stat().st_size if db_path.exists() else 0,
        )

    def retrieve(self, question: str, k: int) -> list[str]:
        config = load_config(self.config_path)
        provider = self.provider
        if self.want_rerank and provider is None:
            provider = "fake"
        result = search_result(
            config,
            question,
            limit=k,
            offline=True,
            decay=True,
            rerank=self.want_rerank,
            provider=provider,
        )
        self.last_in_tokens = 0
        self.last_out_tokens = 0
        return [hit.ext_id for hit in result.hits]

    def close(self) -> None:
        return None


def lodestone_lexical(directory: Path, chat: Chat | None = None) -> LodestoneStrategy:
    return LodestoneStrategy(
        directory, name="lodestone-lexical", lanes=LEXICAL_LANES, embed="none", chat=chat
    )


def lodestone_hybrid(directory: Path, chat: Chat | None = None) -> LodestoneStrategy:
    return LodestoneStrategy(
        directory, name="lodestone-hybrid", lanes=HYBRID_LANES, embed="hash", chat=chat
    )


def lodestone_rerank(directory: Path, chat: Chat | None = None) -> LodestoneStrategy:
    return LodestoneStrategy(
        directory,
        name="lodestone-rerank",
        lanes=HYBRID_LANES,
        embed="hash",
        rerank=True,
        provider="fake",
        chat=chat,
    )


class LodestoneLexical(LodestoneStrategy):
    """Back-compat alias used by Bench I imports."""

    name = "lodestone-lexical"

    def __init__(self, directory: Path) -> None:
        super().__init__(directory, name="lodestone-lexical", lanes=LEXICAL_LANES, embed="none")
