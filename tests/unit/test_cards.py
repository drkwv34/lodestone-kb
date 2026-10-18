# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from lodestone.config import Config, Embed, Source
from lodestone.distill.llm import llm_card
from lodestone.distill.render import embedding_input, render_norm, truncate_head_tail
from lodestone.distill.schema import Card
from lodestone.ingest.pipeline import sync
from lodestone.providers.fake import FakeLLM
from lodestone.storage.records import get_record

VALID = {
    "question": "Why does the latch stall?",
    "summary": "Cycle the power feed.",
    "resolution": "Set CKPT_PREFETCH=4.",
    "entities": ["latch"],
    "code_refs": ["CKPT_PREFETCH"],
}


def test_fr_020_malformed_json_retry_then_valid() -> None:
    chat = FakeLLM(script=["not-json", "{", json.dumps(VALID)])
    card, method = llm_card("Latch", "raw latch text", kind="doc", chat=chat, max_input_chars=1000)
    assert method == "llm"
    assert card.question == VALID["question"]
    assert len(chat.calls) == 3
    assert card.char_spans or card.source_message_ids


def test_fr_020_malformed_json_fallback_heuristic() -> None:
    chat = FakeLLM(script=["{", "{", "{"])
    card, method = llm_card(
        "Latch title",
        "First line. Second sentence about the latch.",
        kind="doc",
        chat=chat,
        max_input_chars=1000,
    )
    assert method == "heuristic"
    assert card.question == "Latch title"
    assert len(chat.calls) == 3


def test_fr_022_head_tail_truncation() -> None:
    short = "abc"
    assert truncate_head_tail(short, 10) == short
    long = "abcdefghij" * 8
    clipped = truncate_head_tail(long, 20)
    assert "\n...\n" in clipped
    assert clipped.startswith(long[:7])
    assert clipped.endswith(long[-8:])
    assert len(clipped) == 20
    assert truncate_head_tail("abcdef", 4) == "abcd"


def test_fr_022_norm_text_and_card_embed_input() -> None:
    card = Card.model_validate(VALID)
    plain = render_norm(card, "plain")
    assert plain == (
        "Why does the latch stall?\nCycle the power feed.\nSet CKPT_PREFETCH=4.\n"
        "systems: latch\ncode: CKPT_PREFETCH"
    )
    xml = render_norm(card, "xml")
    assert "<question>Why does the latch stall?</question>" in xml
    assert embedding_input("RAW_BODY", plain, "card") == [plain]
    assert "RAW_BODY" not in embedding_input("RAW_BODY", plain, "card")
    assert embedding_input("RAW_BODY", plain, "raw") == ["RAW_BODY"]
    assert embedding_input("RAW_BODY", plain, "both") == [plain, "RAW_BODY"]
    assert embedding_input("RAW_BODY", "", "card") == ["RAW_BODY"]


def test_fr_022_embed_source_change_requeues_embeddings_only(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("# Note\nstable body\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    cards = list(database.execute("SELECT id,card_json,norm_text FROM records WHERE kind='doc'"))
    assert cards and cards[0][1]
    for record_id, *_rest in database.execute("SELECT id FROM records"):
        database.execute(
            "INSERT INTO embeddings VALUES(?,'chunk','local',1,X'00000000')", (record_id,)
        )
    database.commit()
    before_cards = list(database.execute("SELECT id,card_json,text FROM records ORDER BY id"))
    config.embed = Embed(source="raw")
    report = sync(database, config)
    assert report.processed == 0
    assert database.execute("SELECT count(*) FROM embeddings").fetchone() == (0,)
    assert (
        list(database.execute("SELECT id,card_json,text FROM records ORDER BY id")) == before_cards
    )


def test_fr_023_cache_hit_ratio_and_model_change(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.md").write_text("# A\nalpha token\n", encoding="utf-8")
    (root / "b.md").write_text("# B\nbeta token\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    first = sync(database, config, chat=FakeLLM())
    cardable = database.execute("SELECT count(*) FROM records WHERE kind='doc'").fetchone()[0]
    assert first.cache_misses == cardable
    assert first.llm_calls == cardable
    second = sync(database, config, chat=FakeLLM())
    assert second.processed == 0
    assert second.llm_calls == 0
    assert second.cache_hits == cardable
    assert second.cache_misses == 0
    assert second.cache_hits / (second.cache_hits + second.cache_misses) == 1.0
    changed = FakeLLM()
    changed.model = "fake-v2"
    third = sync(database, config, chat=changed)
    assert third.llm_calls == cardable
    assert third.cache_misses == cardable
    refreshed = sync(database, config, chat=FakeLLM(model="fake-v2"), refresh_cards=True)
    assert refreshed.llm_calls == cardable


def test_fr_024_provenance_and_get_record(database, tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "guide.md").write_text("# Guide\nVisible claim about the latch.\n", encoding="utf-8")
    config = Config(sources=[Source(name="docs", kind="files", path=root)])
    sync(database, config)
    cards = list(database.execute("SELECT id,card_json FROM records WHERE card_json IS NOT NULL"))
    assert cards
    for record_id, payload in cards:
        card = json.loads(payload)
        assert card["char_spans"] or card["source_message_ids"]
        view = get_record(database, int(record_id))
        assert view["raw_text"]
        assert view["card"] == card
        assert "Visible claim" in str(view["raw_text"])


def test_fr_025_contextual_prefix_is_fts_matchable(database, tmp_path: Path) -> None:
    from lodestone.config import Chunks
    from lodestone.lanes.fts import search

    root = tmp_path / "docs"
    root.mkdir()
    (root / "guide.md").write_text(
        "# Guide\n\n## Install\nActual chunk body about disks.\n", encoding="utf-8"
    )
    config = Config(
        sources=[Source(name="docs", kind="files", path=root)],
        chunks=Chunks(contextualize=True),
    )
    sync(database, config, chat=FakeLLM())
    prefix = database.execute(
        "SELECT context_prefix FROM records WHERE kind='section' LIMIT 1"
    ).fetchone()
    assert prefix and "XYZZY_CONTEXT_TOKEN" in prefix[0]
    hits = search(database, "XYZZY_CONTEXT_TOKEN", lane="fts_card")
    assert hits
    assert search(database, "XYZZY_CONTEXT_TOKEN", lane="fts_raw") == []
