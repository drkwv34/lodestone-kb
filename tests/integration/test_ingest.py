# SPDX-License-Identifier: Apache-2.0
import shutil
import sqlite3
from pathlib import Path

import pytest

from lodestone.config import Config, Source
from lodestone.ingest.pipeline import content_hash, sync
from lodestone.lanes.fts import search
from lodestone.storage.terms import document_count

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"


def test_fr_030_exact_token_ranks_first(database: sqlite3.Connection, tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    shutil.copytree(CORPUS, root)
    config = Config(sources=[Source(name="wiki", kind="files", path=root, exclude=["drafts/**"])])
    assert sync(database, config).processed == 4
    hits = search(database, "ERR_MANIFEST_TIMEOUT")
    assert hits[0].ext_id == "manifest.md"
    assert "ERR_MANIFEST_TIMEOUT" in hits[0].snippet
    assert len(hits) == 1


def test_fr_014_resync_zero_writes_and_single_file_edit(
    database: sqlite3.Connection, tmp_path: Path
) -> None:
    root = tmp_path / "corpus"
    shutil.copytree(CORPUS, root)
    config = Config(sources=[Source(name="wiki", kind="files", path=root, exclude=["drafts/**"])])
    first = sync(database, config)
    assert first.processed == 4
    before = list(database.execute("SELECT * FROM records ORDER BY id"))
    changes = database.total_changes
    traced: list[str] = []
    database.set_trace_callback(traced.append)
    second = sync(database, config)
    database.set_trace_callback(None)
    assert (second.processed, second.unchanged, second.llm_calls) == (0, 4, 0)
    assert database.total_changes == changes
    assert not any(
        query.startswith(("INSERT INTO records", "UPDATE records", "DELETE FROM records"))
        for query in traced
    )
    assert list(database.execute("SELECT * FROM records ORDER BY id")) == before
    (root / "manifest.md").write_text("changed ERR_REPLACED", encoding="utf-8")
    third = sync(database, config)
    assert (third.processed, third.unchanged) == (1, 3)
    after = list(database.execute("SELECT * FROM records ORDER BY id"))
    assert [row[0] for row in after] == [row[0] for row in before]
    assert sum(old != new for old, new in zip(before, after, strict=True)) == 1
    assert search(database, "ERR_MANIFEST_TIMEOUT") == []
    assert search(database, "ERR_REPLACED")[0].ext_id == "manifest.md"
    assert document_count(database) == 4
    assert list(database.execute("SELECT * FROM llm_log")) == []


def test_fr_014_invalid_source_does_not_register(
    database: sqlite3.Connection, tmp_path: Path
) -> None:
    source = Source(name="wiki", kind="files", path=tmp_path, include=["../*.txt"])
    with pytest.raises(ValueError, match="patterns"):
        sync(database, Config(sources=[source]))
    assert list(database.execute("SELECT * FROM sources")) == []
    with pytest.raises(ValueError, match="unique"):
        sync(database, Config(sources=[source, source]))
    with pytest.raises(ValueError, match="files sources"):
        sync(database, Config(sources=[Source(name="x", kind="threads", path=tmp_path)]))


def test_fr_014_hash_normalization_and_version() -> None:
    assert content_hash("café\r\nnext\r") == content_hash("cafe\u0301\nnext\n")
    assert content_hash("a") != content_hash("a", version="file-v1")
    assert content_hash("a") != content_hash("b")
    assert len(content_hash("a")) == 64
