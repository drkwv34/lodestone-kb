# SPDX-License-Identifier: Apache-2.0
import json

from lodestone.config import Config, Retrieval
from lodestone.fusion.pipeline import fused_search
from lodestone.lanes.scope import Scope
from lodestone.providers.fake import FakeLLM
from lodestone.rerank import LLMReranker


def test_fr_039_rerank_permutes_candidate_pool() -> None:
    hits = [(3, "gamma token", 0.1), (1, "alpha token", 0.9), (2, "beta token", 0.5)]
    payload = json.dumps([{"id": 2, "score": 10}, {"id": 3, "score": 8}, {"id": 1, "score": 1}])
    ranked = LLMReranker(FakeLLM(script=[payload])).rerank("token", hits)
    assert [ident for ident, _score in ranked] == [2, 3, 1]
    assert sorted(ident for ident, _score in ranked) == sorted(ident for ident, _s, _f in hits)
    assert all(0 <= score <= 10 for _ident, score in ranked)


def test_fr_039_rerank_fallback_keeps_fused_order(database, record_factory) -> None:
    first = record_factory("alpha unique token first", title="first", ext_id="first.md")
    second = record_factory("alpha unique token second", title="second", ext_id="second.md")
    config = Config(retrieval=Retrieval(lanes=["fts_raw"], candidate_pool=20, rerank_keep=10))
    fused = fused_search(database, config, "alpha", scope=Scope(), rerank=False)
    missing = fused_search(database, config, "alpha", scope=Scope(), rerank=True, chat=None)
    broken = fused_search(
        database, config, "alpha", scope=Scope(), rerank=True, chat=FakeLLM(script=["not-json"])
    )
    assert [hit.id for hit in fused.hits] == [hit.id for hit in missing.hits]
    assert [hit.id for hit in fused.hits] == [hit.id for hit in broken.hits]
    assert missing.notices
    assert broken.notices
    assert first != second


def test_fr_039_explain_includes_rerank_score(database, record_factory) -> None:
    low = record_factory("shared token irrelevant", title="low", ext_id="low.md")
    high = record_factory("shared token important", title="high", ext_id="high.md")
    payload = json.dumps([{"id": high, "score": 10}, {"id": low, "score": 1}])
    config = Config(retrieval=Retrieval(lanes=["fts_raw"]))
    result = fused_search(
        database,
        config,
        "shared",
        scope=Scope(),
        rerank=True,
        explain=True,
        chat=FakeLLM(script=[payload]),
    )
    assert [hit.id for hit in result.hits] == [high, low]
    assert result.packets[0]["explain"]["rerank_score"] == 10
    assert result.packets[1]["explain"]["rerank_score"] == 1
