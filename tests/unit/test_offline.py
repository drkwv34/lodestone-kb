# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

import pytest

from lodestone.config import Config, Source
from lodestone.ingest.pipeline import sync
from lodestone.lanes.vec import search as vec_search
from lodestone.providers import make_chat
from lodestone.providers.chat import OpenAIChat
from lodestone.providers.fake import FakeLLM
from lodestone.providers.offline import OfflineError, offline_scope, set_offline
from lodestone.vectors import HashEmbedder, make_embedder
from lodestone.vectors.openai_compat import OpenAICompatEmbedder


def test_fr_062_offline_guard_hash_embedder_and_remote_raises(
    database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise OSError("network disabled")

    monkeypatch.setattr("socket.socket", blocked)
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text(
        "# Restore\nERR_MANIFEST_TIMEOUT unique_vec_token\n", encoding="utf-8"
    )
    config = Config(sources=[Source(name="docs", kind="files", path=root)], offline=True)
    with offline_scope(True):
        embedder = make_embedder(config, offline=True)
        assert isinstance(embedder, HashEmbedder)
        report = sync(database, config, embedder=embedder)
        assert report.processed >= 1
        result = vec_search(
            database, "unique_vec_token", lane="vec_card", embedder=embedder, limit=5
        )
        assert result.hits
        assert result.hits[0].ext_id == "note.md"
        with pytest.raises(OfflineError):
            OpenAICompatEmbedder(base_url="http://127.0.0.1:1/v1", model="nomic-embed-text")
        with pytest.raises(OfflineError):
            OpenAIChat(base_url="http://127.0.0.1:1/v1", model="gpt")
        with pytest.raises(OfflineError):
            make_chat(config, "config", offline=True)
        assert isinstance(make_chat(config, "fake", offline=True), FakeLLM)
        assert make_chat(config, offline=True) is None
    set_offline(False)
    remote = OpenAICompatEmbedder(
        base_url="http://127.0.0.1:1/v1", model="nomic-embed-text", timeout_s=0.05
    )
    set_offline(True)
    with pytest.raises(OfflineError):
        remote.embed(["hello"])
    remote.close()
