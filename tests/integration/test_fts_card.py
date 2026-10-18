# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from lodestone.config import Config, Source
from lodestone.ingest.pipeline import sync
from lodestone.lanes.fts import search
from lodestone.providers.fake import FakeLLM

CARD = {
    "question": "How does plankton recovery work after a latch stall?",
    "summary": "Run plankton_recovery then clear the latch.",
    "resolution": "",
    "entities": ["plankton"],
    "code_refs": ["plankton_recovery"],
}


def test_fr_031_paraphrase_found_only_by_fts_card(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "latch.md").write_text(
        "The power feed is cycled twice until the handle releases.\n", encoding="utf-8"
    )
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    report = sync(database, config, chat=FakeLLM(script=[json.dumps(CARD)]))
    assert report.llm_calls == 1
    query = "plankton recovery"
    card_hits = search(database, query, lane="fts_card", kinds=["doc"])
    raw_hits = search(database, query, lane="fts_raw", kinds=["doc"])
    assert [hit.ext_id for hit in card_hits] == ["latch.md"]
    assert raw_hits == []
    database.execute("INSERT INTO records_fts(records_fts,rank) VALUES('integrity-check',1)")
    database.execute(
        "INSERT INTO records_card_fts(records_card_fts,rank) VALUES('integrity-check',1)"
    )
