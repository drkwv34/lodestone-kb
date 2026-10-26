# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

from lodestone.config import Config, Source, load_config
from lodestone.ingest.pipeline import sync
from lodestone.ingest.reindex import reindex_workspace
from lodestone.workspace import initialise, sync_workspace


def test_fr_083_reindex_lanes_fts_vec_cards(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\nreindex unique token\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    assert sync(database, config).processed >= 1
    fts_before = int(database.execute("SELECT count(*) FROM records_fts").fetchone()[0])
    cards_before = int(
        database.execute(
            "SELECT count(*) FROM records WHERE card_json IS NOT NULL AND tombstoned=0"
        ).fetchone()[0]
    )
    initialise(tmp_path)
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(
        'schema_version = 1\n[workspace]\ndb_path = ".lodestone/index.db"\n'
        '[[projects]]\nname="default"\nsources=["docs"]\n'
        '[[sources]]\nname="docs"\nkind="files"\npath="docs"\n'
    )
    workspace = load_config(config_path)
    sync_workspace(workspace, offline=True)
    fts = reindex_workspace(workspace, lanes=["fts"], offline=True)
    assert fts["fts_before"] == fts["fts_after"]
    cards = reindex_workspace(workspace, lanes=["cards"], offline=True)
    assert cards["cards_before"] == cards["cards_after"]
    vec = reindex_workspace(workspace, lanes=["vec"], offline=True)
    assert vec["before"] == vec["after"]
    assert fts_before >= 1
    assert cards_before >= 0


def test_nfr_006_pending_derived_resumes_on_sync(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\npending unique token\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    parent = database.execute("SELECT id FROM records WHERE parent_id IS NULL").fetchone()[0]
    with database:
        database.execute(
            "UPDATE records SET derived_state='pending', card_json=NULL, card_method=NULL "
            "WHERE id=?",
            (parent,),
        )
    report = sync(database, config)
    assert report.unchanged >= 1
    state = database.execute(
        "SELECT derived_state, card_json FROM records WHERE id=?", (parent,)
    ).fetchone()
    assert state[0] == "ok"
    assert state[1]
