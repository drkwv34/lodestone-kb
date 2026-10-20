# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import math
import random
import sqlite3

import pytest

from lodestone.config import Config, Embed
from lodestone.providers.chat import ProviderError
from lodestone.storage.costs import log_call
from lodestone.storage.embeddings import (
    delete_for_record,
    pack_vector,
    unpack_vector,
    write_embedding,
)
from lodestone.vectors.backends import BruteForceBackend, SqliteVecBackend, sqlite_vec_available
from lodestone.vectors.embedder import make_embedder
from lodestone.vectors.hash import HASH_DIM, HASH_MODEL, HashEmbedder
from lodestone.vectors.openai_compat import OpenAICompatEmbedder
from tests.http_support import Scripted, embed_body, serve

SAMPLE = "restore hangs after manifest load"
EXPECTED_PREFIX = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.30151134457776363, 0.0]


def _unit(rng: random.Random, dim: int) -> list[float]:
    values = [rng.uniform(-1.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(item * item for item in values)) or 1.0
    return [item / norm for item in values]


def test_fr_061_hash_embedder_deterministic() -> None:
    first = HashEmbedder().embed([SAMPLE])[0]
    second = HashEmbedder().embed([SAMPLE])[0]
    assert len(first) == HASH_DIM
    assert first == second
    assert first[:8] == pytest.approx(EXPECTED_PREFIX)
    empty = HashEmbedder().embed([""])[0]
    assert empty == [0.0] * HASH_DIM
    assert "not semantic" in (HashEmbedder.__doc__ or "").lower()


def test_fr_061_openai_compat_embedder_retry_and_llm_log(database: sqlite3.Connection) -> None:
    vector = [0.6, 0.8]
    with serve(
        [
            Scripted(status=429, body=b'{"error":"rate"}'),
            Scripted(body=embed_body([vector], model="emb")),
        ]
    ) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        embedder = OpenAICompatEmbedder(
            base_url=url,
            model="emb",
            dim=2,
            sleep=lambda _delay: None,
            rng=random.Random(0),  # noqa: S311
            backoff_base=0.0,
            log=lambda op, result: log_call(
                database,
                op=op,
                model=result.model,
                in_tokens=result.in_tokens,
                out_tokens=result.out_tokens,
                latency_ms=result.latency_ms,
                ok=result.ok,
            ),
        )
        got = embedder.embed(["hello"])
        assert embedder.embed([]) == []
        embedder.close()
    assert len(got) == 1 and len(got[0]) == 2
    assert pytest.approx(math.sqrt(sum(item * item for item in got[0]))) == 1.0
    rows = list(database.execute("SELECT op, ok FROM llm_log ORDER BY id"))
    assert rows[0][0] == "embed" and rows[-1][1] == 1
    with serve([Scripted(status=401, body=b"no")]) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        embedder = OpenAICompatEmbedder(
            base_url=url, model="emb", dim=2, sleep=lambda _delay: None, backoff_base=0.0
        )
        with pytest.raises(ProviderError, match="HTTP 401"):
            embedder.embed(["x"])
        embedder.close()


def test_fr_033_backend_parity_1000_vectors() -> None:
    rng = random.Random(0)  # noqa: S311
    dim = 32
    rows = [(index + 1, pack_vector(_unit(rng, dim))) for index in range(1000)]
    query = _unit(rng, dim)
    array_hits = BruteForceBackend(use_numpy=False).query(rows, query, 25)
    numpy_hits = BruteForceBackend(use_numpy=True).query(rows, query, 25)
    assert [hit.record_id for hit in array_hits] == [hit.record_id for hit in numpy_hits]
    for left, right in zip(array_hits, numpy_hits, strict=True):
        assert left.score == pytest.approx(right.score, abs=1e-6)
    if sqlite_vec_available():
        vec_hits = SqliteVecBackend().query(rows, query, 25, model="hash", dim=dim)
        assert [hit.record_id for hit in vec_hits] == [hit.record_id for hit in array_hits]
        for left, right in zip(array_hits, vec_hits, strict=True):
            assert left.score == pytest.approx(right.score, abs=1e-6)


@pytest.mark.skipif(not sqlite_vec_available(), reason="sqlite-vec extra is not installed")
def test_fr_033_sqlite_vec_backend_present() -> None:
    assert sqlite_vec_available()
    rng = random.Random(1)  # noqa: S311
    rows = [(1, pack_vector(_unit(rng, 8))), (2, pack_vector(_unit(rng, 8)))]
    query = _unit(rng, 8)
    brute = BruteForceBackend(use_numpy=False).query(rows, query, 2)
    vec = SqliteVecBackend().query(rows, query, 2, model="nomic", dim=8)
    assert [hit.record_id for hit in vec] == [hit.record_id for hit in brute]
    for left, right in zip(brute, vec, strict=True):
        assert left.score == pytest.approx(right.score, abs=1e-6)


def test_fr_033_pack_unpack_and_backend_edges(database) -> None:
    values = [0.5, -0.5, 0.0, 0.70710677]
    assert unpack_vector(pack_vector(values)) == pytest.approx(values)
    write_id = 1
    database.execute("INSERT INTO sources(name,kind,config_json) VALUES('wiki','files','{}')")
    database.execute(
        "INSERT INTO records(source_id,ext_id,kind,title,text,content_hash,created_at,"
        "updated_at,indexed_at) VALUES(1,'a.md','doc','','t','h','t','t','t')"
    )
    write_embedding(database, write_id, "card", "hash", 4, values)
    delete_for_record(database, write_id)
    assert database.execute("SELECT count(*) FROM embeddings").fetchone()[0] == 0
    query = [1.0, 0.0]
    rows = [(1, pack_vector([1.0, 0.0])), (2, pack_vector([0.0, 1.0, 0.0]))]
    hits = BruteForceBackend(use_numpy=False).query(rows, query, 2)
    assert [hit.record_id for hit in hits] == [1]
    assert BruteForceBackend(use_numpy=False).query([], query, 5) == []
    assert SqliteVecBackend().query(rows, query, 0, model="hash", dim=2) == []
    fallback = SqliteVecBackend().query(rows, query, 1, model="", dim=2)
    assert fallback[0].record_id == 1
    mismatched = SqliteVecBackend().query(rows, query, 1, model="hash", dim=8)
    assert mismatched[0].record_id == 1


def test_fr_061_make_embedder_offline_hash_and_providers() -> None:
    assert make_embedder(Config()) is None
    hashed = make_embedder(Config(embed=Embed(provider="hash", model=HASH_MODEL, dim=HASH_DIM)))
    assert isinstance(hashed, HashEmbedder)
    assert isinstance(make_embedder(Config(), offline=True), HashEmbedder)
    remote = make_embedder(
        Config(
            embed=Embed(
                provider="openai_compat",
                model="nomic-embed-text",
                base_url="http://127.0.0.1:1/v1",
            )
        )
    )
    assert isinstance(remote, OpenAICompatEmbedder)
    remote.close()
