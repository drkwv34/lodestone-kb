# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from lodestone.distill.heuristic import heuristic_card
from lodestone.storage.terms import idf

FIXTURES = Path(__file__).parents[1] / "fixtures" / "cards"


def test_fr_021_golden_heuristic_cards() -> None:
    for name in ("restore", "thread"):
        source = (FIXTURES / f"{name}.md").read_text(encoding="utf-8")
        expected = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        messages = None
        if name == "thread":
            messages = [("m1", "Is NFS stalled?"), ("m2", "Set CKPT_PREFETCH=4 on the mount.")]
        card = heuristic_card("Restore stalls after manifest load", source, messages=messages)
        assert json.loads(card.model_dump_json()) == expected


def test_fr_021_entities_rank_by_idf(database, record_factory) -> None:
    record_factory("Common Word appears often Common Word Common Word")
    record_factory("Zorple only here with Common Word")
    text = "Common Word sits beside Zorple."
    card = heuristic_card("Title", text, connection=database)
    assert idf(database, "zorple") > idf(database, "common")
    assert card.entities[0] == "Zorple"
