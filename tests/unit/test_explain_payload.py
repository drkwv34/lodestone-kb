# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from lodestone import Lodestone
from lodestone.config import Config, Retrieval
from lodestone.fusion.packet import Evidence, Explain, validate_packet
from lodestone.fusion.pipeline import fused_search
from lodestone.lanes.scope import Scope
from tests.helpers import synced_workspace


def test_sdk_search_explain_validates(tmp_path: Path) -> None:
    kb = Lodestone.open(synced_workspace(tmp_path), offline=True)
    result = kb.search("ERR_MANIFEST_TIMEOUT", explain=True)
    assert result.hits
    for hit in result.hits:
        assert isinstance(hit, Evidence)
        dumped = hit.model_dump(by_alias=True)
        Evidence.model_validate(dumped)
        assert hit.explain is not None
        assert isinstance(hit.explain, Explain)
        assert hit.explain.lanes
        assert set(dumped["explain"]) <= {"lanes", "rrf", "decay_factor", "rerank_score", "final"}


def test_fr_042_validate_packet_rejects_flattened_explain(database, record_factory) -> None:
    record_factory("alpha unique explain token")
    config = Config(retrieval=Retrieval(lanes=["fts_raw"]))
    result = fused_search(database, config, "alpha", scope=Scope(), explain=True, decay=False)
    packet = dict(result.packets[0])
    explain = dict(packet["explain"])
    lanes = explain.pop("lanes")
    packet["explain"] = {**lanes, **explain}
    with pytest.raises(ValueError, match="explain extra"):
        validate_packet(packet)
