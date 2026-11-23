# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from pathlib import Path

from lodestone.fusion.packet import Evidence, validate_packet
from tests.helpers import synced_workspace
from tests.integration.test_mcp import _call


def test_search_explain_true(tmp_path: Path) -> None:
    config_path = synced_workspace(tmp_path)
    payload = asyncio.run(
        _call(config_path, "search", {"query": "ERR_MANIFEST_TIMEOUT", "explain": True})
    )
    hits = payload["hits"]
    assert isinstance(hits, list) and hits
    for hit in hits:
        assert isinstance(hit, dict)
        validate_packet(hit)
        evidence = Evidence.model_validate(hit)
        assert evidence.explain is not None
        assert evidence.explain.lanes
        assert "lanes" in hit["explain"]
        assert set(hit["explain"]) <= {"lanes", "rrf", "decay_factor", "rerank_score", "final"}
