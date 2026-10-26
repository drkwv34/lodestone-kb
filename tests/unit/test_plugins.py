# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
from importlib.metadata import EntryPoint
from pathlib import Path

from lodestone.config import Config, Source
from lodestone.ingest.pipeline import sync

DEMO = Path(__file__).resolve().parents[2] / "examples/plugin_demo"


def test_fr_017_example_plugin_loads_through_entry_points(
    database, tmp_path: Path, monkeypatch
) -> None:
    source_file = DEMO / "lodestone_plugin_demo.py"
    lines = source_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 60
    monkeypatch.syspath_prepend(str(DEMO))
    entry = EntryPoint(
        name="notes",
        value="lodestone_plugin_demo:NotesConnector",
        group="lodestone.connectors",
    )
    monkeypatch.setattr(
        "lodestone.connectors.plugins.entry_points",
        lambda group=None: [entry] if group == "lodestone.connectors" else [],
    )
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "hello.note").write_text("plugin unique token lodestone\n", encoding="utf-8")
    config = Config(sources=[Source(name="notes", kind="notes", path=notes)])
    report = sync(database, config)
    assert report.processed >= 1
    row = database.execute("SELECT ext_id, text FROM records WHERE kind='doc'").fetchone()
    assert row[0] == "hello.note"
    assert "plugin unique token" in row[1]
    assert "lodestone_plugin_demo" in sys.modules
