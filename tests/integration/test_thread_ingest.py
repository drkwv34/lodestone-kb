# SPDX-License-Identifier: Apache-2.0
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from lodestone.config import Bursts, Config, Source
from lodestone.ingest.pipeline import sync
from lodestone.lanes.fts import search
from lodestone.providers.fake import FakeLLM
from lodestone.storage.records import get_record

DETAIL = (
    "Checkpoint restore stalls on the NFS mount after the manifest load. "
    "The prefetch window stays full so the loader waits on file handles. "
    "CKPT_PREFETCH needs to drop; the default is too high for this filesystem. "
    "UNIQUE_BURST_TOKEN marks the long rare-term run."
)
RESOLUTION = "Setting CKPT_PREFETCH=4 makes the restore complete on NFS."


def thread_payload(messages: list[dict[str, object]], **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "thread_id": "thread_8f42",
        "channel": "ckpt-support",
        "title": "Restore stalls after manifest load",
        "messages": messages,
    }
    payload.update(extra)
    return payload


def cerebras_messages(extra: list[dict[str, object]] | None = None) -> list[dict[str, object]]:
    messages = [
        {
            "id": "m1",
            "author": "author_a",
            "ts": "2026-07-01T09:14:00Z",
            "text": "sounds good",
        },
        {
            "id": "m2",
            "author": "author_a",
            "ts": "2026-07-01T09:14:10Z",
            "text": "thanks",
        },
        {
            "id": "m3",
            "author": "author_b",
            "ts": "2026-07-01T09:15:00Z",
            "text": DETAIL,
        },
        {
            "id": "m4",
            "author": "author_b",
            "ts": "2026-07-01T09:16:00Z",
            "text": RESOLUTION,
            "reactions": 3,
        },
        {
            "id": "m5",
            "author": "author_c",
            "ts": "2026-07-01T09:17:00Z",
            "text": "ack",
        },
    ]
    if extra:
        messages.extend(extra)
    return messages


def write_source(path: Path, threads: list[dict[str, object]]) -> Path:
    path.write_text("".join(json.dumps(item) + "\n" for item in threads), encoding="utf-8")
    return path


def config_for(path: Path, **kwargs: object) -> Config:
    bursts = kwargs.pop("bursts", None)
    cfg = Config(sources=[Source(name="support", kind="threads", path=path)])
    if bursts is not None:
        cfg.bursts = bursts  # type: ignore[assignment]
    return cfg


def test_fr_012_thread_append_updates_in_place_and_removes_old_bursts(
    database, tmp_path: Path
) -> None:
    path = write_source(tmp_path / "support.jsonl", [thread_payload(cerebras_messages())])
    cfg = config_for(path)
    assert sync(database, cfg).processed == 1
    parent = database.execute(
        "SELECT id,content_hash,updated_at FROM records WHERE kind='thread'"
    ).fetchone()
    old_bursts = list(
        database.execute("SELECT id,ext_id FROM records WHERE kind='burst' ORDER BY seq")
    )
    assert parent is not None
    assert old_bursts
    for record_id in [parent[0], *[row[0] for row in old_bursts]]:
        database.execute(
            "INSERT INTO embeddings VALUES(?,'burst','local',1,X'00000000')", (record_id,)
        )
    database.commit()
    appended = cerebras_messages(
        [
            {
                "id": "m6",
                "author": "author_d",
                "ts": "2026-07-01T10:00:00Z",
                "text": "follow-up note",
            }
        ]
    )
    write_source(path, [thread_payload(appended)])
    report = sync(database, cfg)
    assert (report.processed, report.unchanged) == (1, 0)
    after = database.execute(
        "SELECT id,content_hash,updated_at FROM records WHERE kind='thread'"
    ).fetchone()
    assert after[0] == parent[0]
    assert after[1] != parent[1]
    assert after[2] != parent[2]
    datetime.fromisoformat(after[2])
    leftover = list(
        database.execute("SELECT ext_id,parent_id FROM records WHERE kind='burst' ORDER BY seq")
    )
    assert leftover
    assert {row[1] for row in leftover} == {parent[0]}
    assert database.execute("SELECT count(*) FROM embeddings").fetchone() == (0,)
    assert database.execute("SELECT count(*) FROM records WHERE kind='thread'").fetchone() == (1,)


def test_fr_012_changed_thread_replace_is_atomic(database, tmp_path: Path) -> None:
    path = write_source(tmp_path / "support.jsonl", [thread_payload(cerebras_messages())])
    cfg = config_for(path)
    sync(database, cfg)
    before = list(database.execute("SELECT * FROM records ORDER BY id"))
    hashes = list(database.execute("SELECT id,content_hash FROM records WHERE kind='thread'"))
    database.executescript(
        "CREATE TRIGGER reject_burst BEFORE INSERT ON records WHEN new.kind='burst' "
        "AND new.text LIKE '%FAIL_BURST%' BEGIN SELECT RAISE(ABORT,'injected failure'); END;"
    )
    fail_messages = cerebras_messages()
    fail_messages[2]["text"] = DETAIL + " FAIL_BURST"
    write_source(path, [thread_payload(fail_messages)])
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        sync(database, cfg)
    assert list(database.execute("SELECT * FROM records ORDER BY id")) == before
    assert (
        list(database.execute("SELECT id,content_hash FROM records WHERE kind='thread'")) == hashes
    )


def test_fr_013_burst_records_searchable_via_existing_lanes(database, tmp_path: Path) -> None:
    path = write_source(tmp_path / "support.jsonl", [thread_payload(cerebras_messages())])
    sync(database, config_for(path))
    prefixes = {
        row[0] for row in database.execute("SELECT context_prefix FROM records WHERE kind='burst'")
    }
    assert prefixes
    assert all(prefixes)
    hits = search(database, "UNIQUE_BURST_TOKEN", kinds=["burst"])
    assert hits
    assert all(hit.kind == "burst" for hit in hits)
    assert "UNIQUE_BURST_TOKEN" in hits[0].snippet or hits[0].ext_id.endswith("#burst:1")
    filtered = search(database, "sounds good thanks", kinds=["burst"])
    assert all("sounds good" not in hit.snippet.lower() for hit in filtered)
    high = config_for(path, bursts=Bursts(min_chars=10000, w_idf=0, w_react=0, threshold=1))
    gated = cerebras_messages()
    gated[2]["text"] = DETAIL + " retitled"
    write_source(path, [thread_payload(gated)])
    sync(database, high)
    assert database.execute("SELECT count(*) FROM records WHERE kind='burst'").fetchone() == (0,)


def test_fr_020_thread_cards_via_fake_llm(database, tmp_path: Path) -> None:
    card = {
        "question": "Why does restore stall after manifest load?",
        "summary": "NFS prefetch is too high.",
        "resolution": "Set CKPT_PREFETCH=4.",
        "entities": ["NFS"],
        "code_refs": ["CKPT_PREFETCH"],
    }
    path = write_source(tmp_path / "support.jsonl", [thread_payload(cerebras_messages())])
    report = sync(database, config_for(path), chat=FakeLLM(script=[json.dumps(card)]))
    assert report.cards_llm == 1
    row = database.execute(
        "SELECT card_json,card_method,kind FROM records WHERE kind='thread'"
    ).fetchone()
    stored = json.loads(row[0])
    assert row[1] == "llm"
    assert stored["question"] == card["question"]
    prefix = database.execute(
        "SELECT context_prefix FROM records WHERE kind='burst' LIMIT 1"
    ).fetchone()
    assert prefix and prefix[0] == card["question"]


def test_fr_021_thread_heuristic_resolution_from_last_message(database, tmp_path: Path) -> None:
    path = write_source(tmp_path / "support.jsonl", [thread_payload(cerebras_messages())])
    report = sync(database, config_for(path))
    assert report.cards_heuristic >= 1
    view = get_record(database, "thread_8f42")
    assert view["kind"] == "thread"
    assert view["card"] is not None
    assert view["card_method"] == "heuristic"
    assert view["card"]["resolution"] == "ack"
    assert view["raw_text"]
    assert view["card"]["source_message_ids"] or view["card"]["char_spans"]


def test_fr_011_valid_lines_ingested_and_empty_file(database, tmp_path: Path) -> None:
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    assert sync(database, config_for(empty)).processed == 0
    path = write_source(
        tmp_path / "support.jsonl",
        [thread_payload(cerebras_messages()), thread_payload(cerebras_messages(), thread_id="t2")],
    )
    report = sync(database, config_for(path))
    assert report.processed == 2
    kinds = {row[0] for row in database.execute("SELECT kind FROM records")}
    assert {"thread", "burst"} <= kinds
    unchanged = sync(database, config_for(path))
    assert (unchanged.processed, unchanged.unchanged) == (0, 2)
