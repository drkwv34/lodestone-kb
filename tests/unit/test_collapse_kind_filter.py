# SPDX-License-Identifier: Apache-2.0
from lodestone.config import Config, Retrieval
from lodestone.fusion.pipeline import fused_search
from lodestone.lanes.scope import Scope


def test_kind_burst_never_returns_thread(database, record_factory) -> None:
    parent = record_factory(
        "thread conversation about restore on NFS",
        kind="thread",
        title="Restore stalls",
        ext_id="thread_8f42",
    )
    burst = record_factory(
        "UNIQUE_BURST_TOKEN marks the long rare-term run. Setting CKPT_PREFETCH=4.",
        kind="burst",
        parent_id=parent,
        seq=1,
        ext_id="thread_8f42#burst:1",
        title="Restore stalls",
    )
    config = Config(retrieval=Retrieval(lanes=["fts_raw"]))
    filtered = fused_search(
        database, config, "UNIQUE_BURST_TOKEN", scope=Scope(kinds=["burst"]), decay=False
    )
    assert filtered.hits
    assert all(hit.kind == "burst" for hit in filtered.hits)
    assert all(packet["kind"] == "burst" for packet in filtered.packets)
    assert burst in {hit.id for hit in filtered.hits}
    assert parent not in {hit.id for hit in filtered.hits}
    unfiltered = fused_search(database, config, "UNIQUE_BURST_TOKEN", scope=Scope(), decay=False)
    assert unfiltered.hits
    assert unfiltered.hits[0].id == parent
    assert unfiltered.hits[0].kind == "thread"
    assert burst in {child["id"] for child in unfiltered.packets[0]["children"]}
