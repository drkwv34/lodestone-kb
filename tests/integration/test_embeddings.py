# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

import pytest

from lodestone.config import Config, Embed, Source, load_config
from lodestone.ingest.embeddings import reindex_vectors
from lodestone.ingest.pipeline import sync
from lodestone.ingest.reindex import reindex_workspace
from lodestone.lanes.vec import search as vec_search
from lodestone.vectors.hash import HASH_DIM, HASH_MODEL, HashEmbedder
from lodestone.workspace import initialise, search_result, sync_workspace
from tests.integration.test_thread_ingest import (
    cerebras_messages,
    config_for,
    thread_payload,
    write_source,
)


def test_fr_033_embeddings_deleted_with_records_and_replaced_on_thread_change(
    database, tmp_path: Path
) -> None:
    path = write_source(tmp_path / "threads.jsonl", [thread_payload(cerebras_messages())])
    config = config_for(path)
    config.embed = Embed(provider="hash", model=HASH_MODEL, dim=HASH_DIM)
    embedder = HashEmbedder()
    sync(database, config, embedder=embedder)
    parent = database.execute("SELECT id FROM records WHERE kind='thread'").fetchone()[0]
    kinds = {
        row[0]
        for row in database.execute("SELECT kind FROM embeddings WHERE record_id=?", (parent,))
    }
    assert "card" in kinds
    bursts = list(
        database.execute("SELECT id FROM records WHERE kind='burst' AND parent_id=?", (parent,))
    )
    assert bursts
    burst_ids = {row[0] for row in bursts}
    stored_bursts = {
        row[0] for row in database.execute("SELECT record_id FROM embeddings WHERE kind='burst'")
    }
    assert stored_bursts == burst_ids
    before_id = parent
    payload = thread_payload(
        cerebras_messages(
            [{"id": "m9", "author": "author_z", "ts": "2026-07-01T10:00:00Z", "text": "appended"}]
        )
    )
    write_source(path, [payload])
    sync(database, config, embedder=embedder)
    after = database.execute("SELECT id FROM records WHERE kind='thread'").fetchone()[0]
    assert after == before_id
    live = {row[0] for row in database.execute("SELECT id FROM records WHERE tombstoned=0")}
    stored = {row[0] for row in database.execute("SELECT record_id FROM embeddings")}
    assert stored <= live
    new_bursts = list(
        database.execute("SELECT id FROM records WHERE kind='burst' AND parent_id=?", (after,))
    )
    assert new_bursts
    new_ids = {row[0] for row in new_bursts}
    assert {
        row[0] for row in database.execute("SELECT record_id FROM embeddings WHERE kind='burst'")
    } == new_ids
    assert not (burst_ids - live) & stored
    assert database.execute(
        "SELECT count(*) FROM embeddings WHERE kind='burst' AND record_id=?",
        (new_bursts[0][0],),
    ).fetchone()[0]


def test_fr_033_model_dim_mismatch_treated_as_missing(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\nmismatch_token CKPT_PREFETCH\n", encoding="utf-8")
    config = Config(
        sources=[Source(name="docs", kind="files", path=root)],
        embed=Embed(provider="hash", model=HASH_MODEL, dim=HASH_DIM),
    )
    embedder = HashEmbedder()
    sync(database, config, embedder=embedder)
    database.execute("UPDATE embeddings SET model='other', dim=4")
    database.commit()
    result = vec_search(database, "mismatch_token", lane="vec_card", embedder=embedder)
    assert result.hits == []
    assert any("mismatch" in notice for notice in result.notices)
    assert any("reindex --lanes vec" in notice for notice in result.notices)


def test_fr_033_vec_lanes_skipped_with_notice_when_disabled(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\nplain token\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    disabled = vec_search(database, "plain", lane="vec_card", embedder=None)
    assert disabled.hits == []
    assert disabled.notices == ["vec_card skipped: embeddings disabled"]
    chunk = vec_search(database, "plain", lane="vec_chunk", embedder=None)
    assert chunk.notices == ["vec_chunk skipped: embeddings disabled"]
    with pytest.raises(ValueError, match="limit must be positive"):
        vec_search(database, "plain", lane="vec_card", embedder=None, limit=0)


def test_fr_033_vec_card_and_chunk_hits(
    database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "guide.md").write_text(
        "# Guide\n\nCKPT_PREFETCH unique_card_token in the parent.\n\n## Child\nchunk_only_token\n",
        encoding="utf-8",
    )
    config = Config(
        sources=[Source(name="docs", kind="files", path=root)],
        embed=Embed(provider="hash", model=HASH_MODEL, dim=HASH_DIM),
    )
    embedder = HashEmbedder()
    sync(database, config, embedder=embedder)
    cards = vec_search(database, "unique_card_token", lane="vec_card", embedder=embedder)
    assert cards.hits and cards.hits[0].kind in {"doc", "section"}
    chunks = vec_search(database, "chunk_only_token", lane="vec_chunk", embedder=embedder)
    assert chunks.hits and chunks.hits[0].kind in {"section", "doc"}
    empty = vec_search(
        database, "unique_card_token", lane="vec_card", embedder=embedder, sources=[]
    )
    assert empty.hits == []
    none_kinds = vec_search(
        database, "unique_card_token", lane="vec_card", embedder=embedder, kinds=[]
    )
    assert none_kinds.hits == []
    monkeypatch.setattr("lodestone.lanes.vec.sqlite_vec_available", lambda: False)
    brute = vec_search(
        database,
        "unique_card_token",
        lane="vec_card",
        embedder=embedder,
        sources=["docs"],
        kinds=["doc", "section"],
    )
    assert brute.hits


def test_fr_083_reindex_lanes_vec_row_counts_identical(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.md").write_text("# A\nalpha token\n", encoding="utf-8")
    (root / "b.md").write_text("# B\nbeta token\n", encoding="utf-8")
    config = Config(
        sources=[Source(name="docs", kind="files", path=root)],
        embed=Embed(provider="hash", model=HASH_MODEL, dim=HASH_DIM),
    )
    embedder = HashEmbedder()
    sync(database, config, embedder=embedder)
    before_emb = database.execute("SELECT count(*) FROM embeddings").fetchone()[0]
    before_rec = database.execute("SELECT count(*) FROM records WHERE tombstoned=0").fetchone()[0]
    assert before_emb > 0
    written = reindex_vectors(database, embedder, config.embed.source, batch_size=8)
    database.commit()
    after_emb = database.execute("SELECT count(*) FROM embeddings").fetchone()[0]
    after_rec = database.execute("SELECT count(*) FROM records WHERE tombstoned=0").fetchone()[0]
    assert after_emb == before_emb == written
    assert after_rec == before_rec


def test_fr_033_fr_083_workspace_search_result_and_reindex(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\nworkspace_vec_token CKPT_PREFETCH\n", encoding="utf-8")
    initialise(tmp_path)
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(
        'schema_version = 1\n[workspace]\ndb_path = ".lodestone/index.db"\n'
        '[[projects]]\nname = "default"\nsources = ["docs"]\n[[sources]]\nname = "docs"\n'
        'kind = "files"\npath = "docs"\n'
    )
    config = load_config(config_path)
    report = sync_workspace(config, offline=True)
    assert report.processed >= 1
    result = search_result(config, "workspace_vec_token", lane="vec_card", offline=True)
    assert result.hits
    assert result.lane == "vec_card"
    disabled = search_result(config, "workspace_vec_token", lane="vec_card", offline=False)
    assert disabled.hits == []
    assert any("skipped" in notice for notice in disabled.notices)
    counts = reindex_workspace(config, lanes=["vec"], offline=True)
    assert counts["before"] == counts["after"]
    with pytest.raises(ValueError, match="unknown reindex lane"):
        reindex_workspace(config, lanes=["nope"])
