# SPDX-License-Identifier: Apache-2.0
from lodestone.config import Config, Retrieval
from lodestone.experts import recent, who_knows
from lodestone.lanes.scope import Scope


def test_fr_043_who_knows_returns_expected_top_expert(database, record_factory) -> None:
    maya_one = record_factory(
        "checkpoint restore hangs after manifest load",
        title="maya note",
        author="maya",
        kind="thread",
        updated_at="2026-10-01T00:00:00Z",
        ext_id="maya-1",
    )
    record_factory(
        "checkpoint restore burst on NFS",
        title="maya burst",
        author="maya",
        kind="burst",
        updated_at="2026-10-02T00:00:00Z",
        metadata={"reactions": 2},
        ext_id="maya-2",
    )
    record_factory(
        "checkpoint restore old comment",
        title="owen note",
        author="owen",
        kind="thread",
        updated_at="2025-01-01T00:00:00Z",
        ext_id="owen-1",
    )
    people = who_knows(
        database,
        Config(retrieval=Retrieval(lanes=["fts_raw"])),
        "checkpoint restore",
        scope=Scope(),
        limit=5,
    )
    assert people
    assert people[0].author == "maya"
    assert maya_one in people[0].records
    assert [person.author for person in people[:2]] == ["maya", "owen"]


def test_fr_044_recent_deterministic_order(database, record_factory) -> None:
    older = record_factory("body", updated_at="2026-01-01T00:00:00Z", ext_id="old.md")
    newer = record_factory("body", updated_at="2026-10-01T00:00:00Z", ext_id="new.md")
    same_a = record_factory("body", updated_at="2026-10-21T00:00:00Z", ext_id="tie-a.md")
    same_b = record_factory("body", updated_at="2026-10-21T00:00:00Z", ext_id="tie-b.md")
    hits = recent(database, Scope(), limit=10)
    ids = [hit.id for hit in hits]
    assert ids[:2] == [same_b, same_a]
    assert ids.index(newer) < ids.index(older)
