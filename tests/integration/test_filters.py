# SPDX-License-Identifier: Apache-2.0
import random
from datetime import UTC, datetime, timedelta

import pytest

from lodestone.config import Config, Retrieval
from lodestone.fusion.pipeline import fused_search
from lodestone.lanes.fts import search
from lodestone.lanes.scope import Scope, parse_metadata


def test_fr_041_metadata_filter_parser() -> None:
    assert parse_metadata(None) is None
    assert parse_metadata(["channel=ops", "lang=py"]) == {"channel": "ops", "lang": "py"}
    with pytest.raises(ValueError, match="key=value"):
        parse_metadata(["nocolon"])
    with pytest.raises(ValueError, match="identifiers"):
        parse_metadata(["not-a-key=1"])


def test_fr_041_filters_property_500_combinations(database, record_factory) -> None:
    now = datetime(2026, 6, 1, tzinfo=UTC)
    sources = ["wiki", "code", "chat"]
    kinds = ["doc", "section", "thread"]
    authors = ["maya", "owen", "kai"]
    keys = ["channel", "lang"]
    records: list[dict[str, object]] = []
    for index in range(36):
        source = sources[index % 3]
        kind = kinds[index % 3]
        author = authors[index % 3]
        stamp = (now + timedelta(days=index)).isoformat()
        meta_key = keys[index % 2]
        meta_value = f"v{index % 4}"
        ident = record_factory(
            f"needle body {index}",
            source=source,
            kind=kind,
            author=author,
            authors=[author],
            updated_at=stamp,
            metadata={meta_key: meta_value, "uri": f"file://{source}/{index}"},
            ext_id=f"{source}-{index}",
        )
        records.append(
            {
                "id": ident,
                "source": source,
                "kind": kind,
                "author": author,
                "updated_at": stamp,
                "metadata": {meta_key: meta_value},
            }
        )
    generator = random.Random(20261021)  # noqa: S311 - reproducible filters, not cryptography
    config = Config(retrieval=Retrieval(lanes=["fts_raw"]))
    for _ in range(500):
        source = generator.choice([None, [], [generator.choice(sources)], sources[:2]])
        kinds_f = generator.choice([None, [], [generator.choice(kinds)], kinds[:2]])
        authors_f = generator.choice([None, [], [generator.choice(authors)], authors[:2]])
        since = generator.choice([None, (now + timedelta(days=10)).isoformat()[:10]])
        until = generator.choice([None, (now + timedelta(days=20)).isoformat()[:10]])
        meta_key = generator.choice(keys)
        metadata = generator.choice([None, {}, {meta_key: f"v{generator.randrange(4)}"}])
        scope = Scope(
            sources=source,
            kinds=kinds_f,
            authors=authors_f,
            since=since,
            until=until,
            metadata=metadata,
        )
        fused = fused_search(database, config, "needle", scope=scope, decay=False)
        lane_hits = search(database, "needle", scope=scope, lane="fts_raw")
        for hit in list(fused.hits) + list(lane_hits):
            row = next(item for item in records if item["id"] == hit.id)
            if source is not None:
                assert hit.source in source
            if kinds_f is not None:
                assert hit.kind in kinds_f
            if authors_f is not None:
                assert row["author"] in authors_f
            if since is not None:
                assert str(row["updated_at"]) >= since
            if until is not None:
                bound = until if len(until) > 10 else until + "T23:59:59.999999Z"
                assert str(row["updated_at"]) <= bound
            if metadata:
                meta = row["metadata"]
                assert isinstance(meta, dict)
                assert all(meta.get(key) == value for key, value in metadata.items())
        if source == [] or kinds_f == [] or authors_f == [] or metadata == {}:
            assert fused.hits == []
            assert lane_hits == []
