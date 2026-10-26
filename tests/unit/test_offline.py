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


def test_fr_062_offline_ingest_search_bench_socket_blocked(
    database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise OSError("network disabled")

    monkeypatch.setattr("socket.socket", blocked)
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Restore\nERR_MANIFEST_TIMEOUT unique\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)], offline=True)
    with offline_scope(True):
        report = sync(database, config, embedder=make_embedder(config, offline=True))
        assert report.processed >= 1
        from lodestone.lanes.fts import search as fts_search

        hits = fts_search(database, "ERR_MANIFEST_TIMEOUT", lane="fts_raw", limit=5)
        assert hits
    from lodestone.bench.runner import run_bench
    from lodestone.bench.synth import generate

    corpus = generate(tmp_path / "corpus", seed=1, threads=6)
    run = run_bench(
        corpus=corpus.directory,
        evalset=corpus.evalset,
        out=tmp_path / "run",
        strategies="bm25-chunks,lodestone-lexical",
        k=5,
        generated_at="2026-01-02T00:00:00+00:00",
    )
    assert {item.name: item.status for item in run.strategies}["bm25-chunks"] == "ok"
    assert {item.name: item.status for item in run.strategies}["lodestone-lexical"] == "ok"


def test_nfr_010_offline_zero_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise OSError("network disabled")

    monkeypatch.setattr("socket.socket", blocked)
    from lodestone.config import load_config
    from lodestone.workspace import initialise, search_result, sync_workspace

    initialise(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\nprivacy token\n", encoding="utf-8")
    path = tmp_path / "lodestone.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("sources = []", 'sources = ["docs"]')
        + '\n[[sources]]\nname="docs"\nkind="files"\npath="docs"\n',
        encoding="utf-8",
    )
    config = load_config(path)
    sync_workspace(config, offline=True)
    result = search_result(config, "privacy", offline=True)
    assert result.hits


def test_nfr_010_data_flow_table_present() -> None:
    text = Path(__file__).resolve().parents[2].joinpath("docs/privacy.md").read_text()
    assert "Data-flow table" in text
    for command in ("sync", "search", "ask", "mcp", "bench"):
        assert command in text
    assert "--offline" in text or "`--offline`" in text
