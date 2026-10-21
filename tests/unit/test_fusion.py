# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta

import pytest

from lodestone.config import Config, Decay, Retrieval
from lodestone.fusion.collapse import Ranked, collapse
from lodestone.fusion.decay import apply_decay, decay_factor
from lodestone.fusion.expand import neighbours
from lodestone.fusion.packet import evidence_schema, validate_packet
from lodestone.fusion.pipeline import fused_search
from lodestone.fusion.rrf import rrf
from lodestone.lanes.scope import Scope


def test_fr_035_rrf_rejects_non_positive_k_and_dedupes_ranks() -> None:
    with pytest.raises(ValueError, match="k"):
        rrf({"a": [1]}, k=0)
    fused = rrf({"a": [7, 7, 8]}, {"a": 1.0}, k=60)
    assert fused[7].lanes["a"].rank == 1
    assert fused[8].lanes["a"].rank == 3


def test_fr_035_rrf_reproduces_cerebras_figure() -> None:
    lists = {
        "a": [1, 42],
        "b": [1, 2, 42],
        "c": [42],
        "d": [1, 2, 3, 4, 42],
        "e": [1, 2, 3, 4, 42],
        "f": [1, 2, 3],
    }
    fused = rrf(lists, {lane: 1.0 for lane in lists}, k=60)
    assert fused[42].rrf == pytest.approx(0.0792, abs=0.0001)


def test_fr_036_decay_orders_threads_and_respects_floor() -> None:
    now = datetime(2026, 10, 21, tzinfo=UTC)
    new_age = 14 / 1
    old_age = 8 * 30
    new_factor = decay_factor(new_age, 120, 0.4)
    old_raw = 0.5 ** (old_age / 120)
    old_factor = decay_factor(old_age, 120, 0.4)
    assert new_factor > old_factor
    assert old_raw < 0.4
    assert old_factor == 0.4
    table = {"thread": Decay(half_life_days=120, floor=0.4)}
    newer, newer_factor = apply_decay(
        0.0792, (now - timedelta(days=14)).isoformat(), kind="thread", table=table, now=now
    )
    older, older_factor = apply_decay(
        0.0792, (now - timedelta(days=240)).isoformat(), kind="thread", table=table, now=now
    )
    assert newer > older
    assert older_factor == 0.4
    assert newer_factor == pytest.approx(new_factor)
    raw, factor = apply_decay(
        0.0792,
        (now - timedelta(days=240)).isoformat(),
        kind="thread",
        table=table,
        now=now,
        enabled=False,
    )
    assert factor == 1.0
    assert raw == 0.0792
    future, future_factor = apply_decay(
        1.0, (now + timedelta(days=10)).isoformat(), kind="thread", table=table, now=now
    )
    assert future_factor == 1.0
    assert future == 1.0


def test_fr_036_no_decay_restores_raw_fused_order(database, record_factory) -> None:
    now = datetime(2026, 10, 21, tzinfo=UTC)
    old = record_factory(
        "alpha thread body",
        kind="thread",
        title="alpha alpha",
        updated_at=(now - timedelta(days=240)).isoformat(),
        ext_id="old",
    )
    new = record_factory(
        "alpha thread body",
        kind="thread",
        title="new",
        updated_at=(now - timedelta(days=14)).isoformat(),
        ext_id="new",
    )
    config = Config(
        retrieval=Retrieval(
            lanes=["fts_raw"], decay={"thread": Decay(half_life_days=120, floor=0.4)}
        )
    )
    decayed = fused_search(
        database, config, "alpha", scope=Scope(), decay=True, now=now, explain=True
    )
    raw = fused_search(database, config, "alpha", scope=Scope(), decay=False, now=now, explain=True)
    assert [hit.id for hit in decayed.hits[:2]] == [new, old]
    assert raw.packets[0]["explain"]["decay_factor"] == 1.0


def test_fr_037_collapse_and_per_source_cap(database, record_factory) -> None:
    parent = record_factory("parent file token", kind="doc", ext_id="parent.md")
    children = [
        record_factory(
            f"chunk {index} token",
            kind="section",
            parent_id=parent,
            seq=index,
            ext_id=f"parent.md#section:{index}",
            title=f"H{index}",
        )
        for index in range(6)
    ]
    config = Config(retrieval=Retrieval(lanes=["fts_raw"], max_per_source=3, candidate_pool=20))
    result = fused_search(database, config, "token", scope=Scope(), decay=False)
    assert [hit.id for hit in result.hits] == [parent]
    child_ids = {child["id"] for child in result.packets[0]["children"]}
    assert child_ids == set(children)
    extras = [
        record_factory(f"other {index} token", kind="doc", ext_id=f"other-{index}.md")
        for index in range(6)
    ]
    capped = fused_search(database, config, "token", scope=Scope(), decay=False)
    sources = [hit.source for hit in capped.hits]
    assert sources.count("wiki") <= 3
    ranked = [
        Ranked(ident, None, "wiki" if ident < 10 else "code", 1.0 - ident / 100, "2026-10-17")
        for ident in range(12)
    ]
    collapsed = collapse(ranked, max_per_source=3, pool=20)
    assert len([item for item in collapsed if item.source == "wiki"]) <= 3
    assert len(collapsed) <= 20
    assert extras


def test_fr_038_neighbour_expansion_edge_cases(database, record_factory) -> None:
    parent = record_factory("outline", kind="doc", ext_id="doc.md")
    first = record_factory("one", kind="section", parent_id=parent, seq=0, title="Intro")
    middle = record_factory("two", kind="section", parent_id=parent, seq=1, title="Body")
    last = record_factory("three", kind="section", parent_id=parent, seq=2, title="End")
    mid_neighbours = neighbours(database, middle, n=1, max_chars=4000)
    assert [item["id"] for item in mid_neighbours] == [first, middle, last]
    first_neighbours = neighbours(database, first, n=1, max_chars=4000)
    assert [item["id"] for item in first_neighbours] == [first, middle]
    last_neighbours = neighbours(database, last, n=1, max_chars=4000)
    assert [item["id"] for item in last_neighbours] == [middle, last]
    database.execute("DELETE FROM records WHERE id=?", (first,))
    missing = neighbours(database, middle, n=1, max_chars=4000)
    assert first not in {item["id"] for item in missing}
    assert neighbours(database, parent, n=1) == []
    assert neighbours(database, 999999, n=1) == []
    tiny = neighbours(database, last, n=1, max_chars=1)
    assert sum(len(item["snippet"]) for item in tiny) <= 1


def test_fr_040_explain_contributions_sum_to_fused_score(database, record_factory) -> None:
    record_factory("alpha beta unique token")
    config = Config(retrieval=Retrieval(lanes=["fts_raw", "fts_card"]))
    result = fused_search(database, config, "alpha", scope=Scope(), explain=True, decay=True)
    assert result.packets
    explain = result.packets[0]["explain"]
    contributions = [
        info["contribution"] for name, info in explain.items() if isinstance(info, dict)
    ]
    assert sum(contributions) == pytest.approx(explain["rrf"], abs=1e-12)
    assert explain["rrf"] * explain["decay_factor"] == pytest.approx(explain["final"], abs=1e-9)
    assert explain["final"] == pytest.approx(result.hits[0].score, abs=1e-9)


def test_fr_042_evidence_packet_schema(database, record_factory) -> None:
    record_factory("schema token", metadata={"uri": "file://wiki/schema.md"})
    config = Config(retrieval=Retrieval(lanes=["fts_raw"]))
    result = fused_search(database, config, "schema", scope=Scope(), explain=True)
    schema = evidence_schema()
    assert schema["title"] == "evidence.v1"
    packet = {key: value for key, value in result.packets[0].items() if key != "explain"}
    validate_packet(packet, schema)
    for key in schema["required"]:
        assert key in packet
