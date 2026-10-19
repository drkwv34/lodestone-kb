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
    hits = search(database, "ERR_MANIFEST_TIMEOUT", kinds=["doc"])
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
    before = list(database.execute("SELECT * FROM records WHERE parent_id IS NULL ORDER BY id"))
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
    assert (
        list(database.execute("SELECT * FROM records WHERE parent_id IS NULL ORDER BY id"))
        == before
    )
    (root / "manifest.md").write_text("changed ERR_REPLACED", encoding="utf-8")
    third = sync(database, config)
    assert (third.processed, third.unchanged) == (1, 3)
    after = list(database.execute("SELECT * FROM records WHERE parent_id IS NULL ORDER BY id"))
    assert [row[0] for row in after] == [row[0] for row in before]
    assert sum(old != new for old, new in zip(before, after, strict=True)) == 1
    assert search(database, "ERR_MANIFEST_TIMEOUT", kinds=["doc"]) == []
    assert search(database, "ERR_REPLACED")[0].ext_id == "manifest.md"
    assert document_count(database) == 8
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
    with pytest.raises(ValueError, match="threads source path must be a file"):
        sync(database, Config(sources=[Source(name="x", kind="threads", path=tmp_path)]))


def test_fr_014_hash_normalization_and_version() -> None:
    assert content_hash("café\r\nnext\r") == content_hash("cafe\u0301\nnext\n")
    assert content_hash("a") != content_hash("a", version="file-v1")
    assert content_hash("a") != content_hash("b")
    assert len(content_hash("a")) == 64


def test_fr_014_edit_counts_chunking_and_replaces_children_atomically(
    database: sqlite3.Connection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import patch

    from lodestone.chunking import markdown
    from lodestone.config import Chunks

    root = tmp_path / "documents"
    root.mkdir()
    (root / "a.md").write_text("# A\nOld word\n## Extra\nretired_token\n")
    (root / "b.md").write_text("# B\nStable word\n")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    assert sync(database, config).processed == 2
    parent = database.execute("SELECT id FROM records WHERE ext_id='a.md'").fetchone()[0]
    child_ids = {
        row[0] for row in database.execute("SELECT id FROM records WHERE parent_id=?", (parent,))
    }
    for record_id in [parent, *child_ids]:
        database.execute(
            "INSERT INTO embeddings VALUES(?,'chunk','local',1,X'00000000')", (record_id,)
        )
    database.commit()
    with patch.object(markdown, "chunk", wraps=markdown.chunk) as counted:
        assert sync(database, config).processed == 0
        assert counted.call_count == 0
        (root / "a.md").write_text("# A\nnew_token\n")
        report = sync(database, config)
        assert (report.processed, report.unchanged, report.llm_calls) == (1, 1, 0)
        assert counted.call_count == 1
    assert database.execute("SELECT id FROM records WHERE ext_id='a.md'").fetchone() == (parent,)
    children = list(
        database.execute("SELECT seq,title,text FROM records WHERE parent_id=?", (parent,))
    )
    assert children == [(0, "A", "# A\nnew_token\n")]
    assert database.execute("SELECT count(*) FROM embeddings").fetchone() == (0,)
    assert search(database, "retired_token") == []
    assert database.execute("SELECT df FROM term_stats WHERE term='new_token'").fetchone() == (2,)
    before = list(database.execute("SELECT * FROM records ORDER BY id"))
    stats = list(database.execute("SELECT * FROM term_stats ORDER BY term"))
    database.executescript(
        "CREATE TRIGGER reject_child BEFORE INSERT ON records WHEN new.kind='section' "
        "AND new.text LIKE '%FAIL%' BEGIN SELECT RAISE(ABORT,'injected failure'); END;"
    )
    (root / "a.md").write_text("# A\nFAIL\n")
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        sync(database, config)
    assert list(database.execute("SELECT * FROM records ORDER BY id")) == before
    assert list(database.execute("SELECT * FROM term_stats ORDER BY term")) == stats
    database.execute("DROP TRIGGER reject_child")
    config.chunks = Chunks(target_tokens=10, max_tokens=20)
    assert sync(database, config).processed == 2


def test_fr_014_tombstone_restore_prune_and_unavailable_root(
    database: sqlite3.Connection, tmp_path: Path
) -> None:
    root = tmp_path / "documents"
    root.mkdir()
    file = root / "gone.md"
    raw = "# Gone\nremoved_word\n"
    file.write_text(raw)
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    parent = database.execute("SELECT id FROM records WHERE parent_id IS NULL").fetchone()[0]
    file.unlink()
    report = sync(database, config)
    assert (report.tombstoned, report.pruned) == (1, 0)
    assert database.execute("SELECT sum(tombstoned),count(*) FROM records").fetchone() == (2, 2)
    assert document_count(database) == 0
    assert search(database, "removed_word") == []
    assert database.execute("SELECT count(*) FROM term_stats").fetchone() == (0,)
    changes = database.total_changes
    assert sync(database, config).tombstoned == 0
    assert database.total_changes == changes
    file.write_text(raw)
    assert sync(database, config).processed == 1
    assert database.execute("SELECT id FROM records WHERE parent_id IS NULL").fetchone() == (
        parent,
    )
    assert len(search(database, "removed_word")) == 2
    # A skipped file is not evidence of deletion.
    file.write_bytes(b"\x00binary")
    assert sync(database, config, prune=True).pruned == 0
    assert len(search(database, "removed_word")) == 2
    file.unlink()
    report = sync(database, config, prune=True)
    assert (report.tombstoned, report.pruned) == (1, 1)
    assert database.execute("SELECT count(*) FROM records").fetchone() == (0,)
    assert list(database.execute("SELECT * FROM record_terms")) == []
    assert list(database.execute("SELECT * FROM records_vocab")) == []
    database.execute("INSERT INTO records_fts(records_fts,rank) VALUES('integrity-check',1)")
    root.rmdir()
    with pytest.raises(FileNotFoundError):
        sync(database, config, prune=True)


def test_fr_010_fr_016_code_parent_outline_and_children(
    database: sqlite3.Connection, tmp_path: Path
) -> None:
    from lodestone.connectors.files import CODE_KINDS

    for language in CODE_KINDS:
        (tmp_path / f"unit.{language}").write_text("def example():\n    return 1\n")
    config = Config(sources=[Source(name="code", kind="files", path=tmp_path)])
    assert sync(database, config).processed == 8
    assert database.execute("SELECT count(*) FROM records WHERE kind='code_file'").fetchone() == (
        8,
    )
    assert database.execute("SELECT count(*) FROM records WHERE kind='code'").fetchone()[0] >= 8
    assert database.execute(
        "SELECT context_prefix FROM records WHERE ext_id='unit.py'"
    ).fetchone() == ("def example():",)
    assert database.execute(
        "SELECT count(*) FROM records c JOIN records p ON c.parent_id=p.id "
        "WHERE c.kind='code' AND p.kind<>'code_file'"
    ).fetchone() == (0,)


def test_fr_014_incomplete_scan_preserves_missing_records(
    database: sqlite3.Connection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lodestone.connectors.files import FilesConnector

    root = tmp_path / "documents"
    root.mkdir()
    for name in ("one", "two"):
        (root / f"{name}.md").write_text(f"# {name}\nretained_token\n")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    before = list(database.execute("SELECT * FROM records ORDER BY id"))
    original = FilesConnector.discover

    def interrupted(self, source):
        yield next(original(self, source))
        from lodestone.connectors.files import discovery_error

        discovery_error(PermissionError("unreadable subtree"))

    monkeypatch.setattr(FilesConnector, "discover", interrupted)
    with pytest.raises(PermissionError, match="unreadable subtree"):
        sync(database, config, prune=True)
    assert list(database.execute("SELECT * FROM records ORDER BY id")) == before
    assert len(search(database, "retained_token")) == 4
