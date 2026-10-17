# SPDX-License-Identifier: Apache-2.0
import sqlite3
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lodestone.config import Config, Project, Source, Workspace
from lodestone.ingest.pipeline import sync
from lodestone.workspace import search_workspace


def test_fr_003_project_scope_property_200_queries(
    database: sqlite3.Connection, tmp_path: Path
) -> None:
    roots = [tmp_path / name for name in ("a", "b")]
    for name, root in zip(("a", "b"), roots, strict=True):
        root.mkdir()
        (root / "file.md").write_text(f"# {name}\nneedle shared {name}_only\n")
    config = Config(
        workspace=Workspace(db_path=tmp_path / "index.db", default_project="a"),
        sources=[
            Source(name=name, kind="files", path=root)
            for name, root in zip(("a", "b"), roots, strict=True)
        ],
        projects=[
            Project(name="default", sources=["a", "b"]),
            Project(name="a", sources=["a"]),
            Project(name="b", sources=["b"]),
            Project(name="empty"),
        ],
    )
    assert sync(database, config, project="default").processed == 2
    assert {hit.source for hit in search_workspace(config, "needle")} == {"a"}
    assert search_workspace(config, "needle", project="empty") == []
    assert search_workspace(config, "needle", project="a", sources=["b"]) == []
    assert database.execute("SELECT count(*) FROM project_sources").fetchone() == (4,)
    calls = 0

    @settings(max_examples=200, deadline=None)
    @given(
        suffix=st.text(max_size=80),
        project=st.sampled_from(["a", "b", "empty", "default"]),
        source_filter=st.sampled_from([None, [], ["a"], ["b"], ["a", "b"]]),
        lane=st.sampled_from(["fts_raw", "fts_rare"]),
    )
    def isolated(suffix: str, project: str, source_filter: list[str] | None, lane: str) -> None:
        nonlocal calls
        calls += 1
        # Search the actual workspace boundary, including default scope and SQL limit.
        config.retrieval.rare_idf = 0
        hits = search_workspace(
            config, "needle " + suffix, project=project, sources=source_filter, lane=lane, limit=1
        )
        allowed = config.scoped_sources(project, source_filter)
        assert all(hit.source in allowed for hit in hits)
        assert bool(hits) == bool(allowed)

    isolated()
    assert calls == 200
    with pytest.raises(ValueError, match="unknown project"):
        search_workspace(config, "needle", project="missing")
    with pytest.raises(ValueError, match="unknown source"):
        search_workspace(config, "needle", sources=["missing"])
    (roots[1] / "file.md").write_text("# B\nchanged_only\n")
    assert sync(database, config, project="a").processed == 0
    assert search_workspace(config, "b_only", project="b")
    assert sync(database, config, project="b").processed == 1
    assert search_workspace(config, "b_only", project="b") == []


def test_fr_004_toml_source_removal_reconciles_registry(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "file.md").write_text("retained_token")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    assert database.execute("SELECT count(*) FROM records").fetchone() == (2,)
    sync(database, Config())
    for query in (
        "SELECT count(*) FROM sources",
        "SELECT count(*) FROM records",
        "SELECT count(*) FROM records_vocab",
        "SELECT count(*) FROM term_stats",
        "SELECT count(*) FROM record_terms",
        "SELECT count(*) FROM project_sources",
    ):
        assert database.execute(query).fetchone() == (0,)
