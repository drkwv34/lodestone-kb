# SPDX-License-Identifier: Apache-2.0
import math
import random

import pytest

from lodestone.lanes.fts import sanitise, search
from lodestone.storage.terms import document_count, idf, rare_terms
from lodestone.tokenize import tokenize


def test_fr_030_sanitiser_fuzz_1000_strings(database, record_factory) -> None:
    record_factory("ERR_MANIFEST_TIMEOUT café alpha beta foo-bar")
    generator = random.Random(20261017)  # noqa: S311 - reproducible fuzz, not cryptography
    alphabet = list("\"'{}():*+-_ AND OR NOT NEAR /\\\x00\n") + [
        chr(generator.randrange(0x110000)) for _ in range(256)
    ]
    cases = ["", "\x00", '"', '""', "*", "OR", "NOT", "NEAR(x)", "' OR 1=1 --", '"foo"*']
    cases.extend(
        "".join(generator.choice(alphabet) for _ in range(generator.randrange(120)))
        for _ in range(990)
    )
    assert len(cases) == 1000
    for query in cases:
        search(database, query)
    assert database.execute("SELECT count(*) FROM records").fetchone() == (1,)
    assert search(database, " ".join(["alpha"] * 2000))


def test_fr_030_phrases_prefix_or_and_title_weights(database, record_factory) -> None:
    title_hit = record_factory("neutral", title="alpha beta")
    body_hit = record_factory("alpha beta", title="neutral")
    separated = record_factory("alpha separated beta")
    record_factory("alphabet")
    assert search(database, "alpha")[0].id == title_hit
    assert {hit.id for hit in search(database, '"alpha beta"')} == {title_hit, body_hit}
    assert len(search(database, "alph*")) == 4
    assert len(search(database, "alpha missing")) == 3
    assert separated not in {hit.id for hit in search(database, '"alpha beta"')}
    assert sanitise("{norm_text}:alpha OR beta") == (
        '{title text} : ("norm_text" OR "alpha" OR "or" OR "beta")'
    )
    record_factory("nothing")
    database.execute("UPDATE records SET norm_text='CARD_ONLY'")
    assert search(database, "CARD_ONLY") == []
    with pytest.raises(ValueError, match="lane"):
        search(database, "alpha", lane="invalid")
    with pytest.raises(ValueError, match="limit"):
        search(database, "alpha", limit=0)


def test_fr_032_idf_hand_computed_and_distinct_df(database, record_factory) -> None:
    record_factory("shared shared unique café", title="shared")
    record_factory("shared common")
    record_factory("common")
    assert document_count(database) == 3
    assert database.execute("SELECT df FROM term_stats WHERE term='shared'").fetchone() == (2,)
    assert idf(database, "shared") == pytest.approx(math.log(1.6))
    assert idf(database, "unique") == pytest.approx(math.log(8 / 3))
    assert idf(database, "absent") == pytest.approx(math.log(8))
    assert idf(database, "cafe") == pytest.approx(math.log(8 / 3))
    assert rare_terms(database, ["unique", "absent", "shared"], threshold=0.9) == ["unique"]
    assert rare_terms(database, ["unique", "shared"], df_ratio=0.34) == ["unique"]
    assert rare_terms(database, ["unique"], threshold=4) == []


def test_fr_032_rare_lane_requires_rare_query_term(database, record_factory) -> None:
    rare_id = record_factory("ERR_MANIFEST_TIMEOUT")
    for _ in range(100):
        record_factory("sounds good, thanks")
    assert idf(database, "err_manifest_timeout") > 4
    assert [
        hit.id
        for hit in search(database, "sounds good thanks ERR_MANIFEST_TIMEOUT", lane="fts_rare")
    ] == [rare_id]
    assert search(database, "sounds good thanks", lane="fts_rare") == []
    assert search(database, "unknown", lane="fts_rare") == []
    assert search(database, "ERR_MANIFEST_TIMEOUT", lane="fts_rare", sources=["elsewhere"]) == []


def test_fr_032_triggers_edit_tombstone_delete_and_rollback(database, record_factory) -> None:
    first = record_factory("old old", title="same")
    second = record_factory("same")
    database.commit()
    database.execute("UPDATE records SET text='fresh', norm_text='card_only' WHERE id=?", (first,))
    assert search(database, "old") == []
    assert [hit.id for hit in search(database, "fresh")] == [first]
    assert dict(database.execute("SELECT term,df FROM term_stats")) == {"fresh": 1, "same": 2}
    assert "card_only" not in dict(database.execute("SELECT term,df FROM term_stats"))
    database.execute("UPDATE records SET tombstoned=1 WHERE id=?", (first,))
    assert document_count(database) == 1
    assert search(database, "fresh") == []
    assert dict(database.execute("SELECT term,df FROM term_stats")) == {"same": 1}
    database.execute("UPDATE records SET tombstoned=0 WHERE id=?", (first,))
    database.commit()
    before = list(database.execute("SELECT term,df FROM term_stats ORDER BY term"))
    with pytest.raises(RuntimeError), database:
        database.execute("UPDATE records SET text='rollback' WHERE id=?", (first,))
        database.execute("DELETE FROM records WHERE id=?", (second,))
        raise RuntimeError("injected interruption")
    assert list(database.execute("SELECT term,df FROM term_stats ORDER BY term")) == before
    assert document_count(database) == 2
    assert search(database, "rollback") == []
    assert search(database, "fresh")[0].id == first
    database.execute("INSERT INTO records_fts(records_fts,rank) VALUES('integrity-check',1)")
    database.execute("DELETE FROM sources")
    assert list(database.execute("SELECT * FROM term_stats")) == []
    assert list(database.execute("SELECT * FROM record_terms")) == []
    assert document_count(database) == 0
    assert search(database, "fresh same") == []


def test_fr_032_tokenizer_matches_stats(database, record_factory) -> None:
    text = "Café cafe\u0301 NAÏVE Ελληνικά 東京 ERR_MANIFEST_TIMEOUT foo-bar camelCase"
    record_factory(text)
    assert set(tokenize(text)) == {
        row[0] for row in database.execute("SELECT term FROM term_stats")
    }


def test_fr_041_source_kind_filters_before_limit(database, record_factory) -> None:
    record_factory("needle needle needle", source="outside", kind="thread")
    wanted = record_factory("needle", source="wiki", kind="doc")
    record_factory("needle", source="wiki", kind="section")
    record_factory("needle", source="O'Reilly", kind="doc")
    assert search(database, "needle", sources=["wiki"], kinds=["doc"], limit=1)[0].id == wanted
    for source in (
        None,
        [],
        ["wiki"],
        ["outside"],
        ["O'Reilly"],
        ["wiki", "outside"],
        ["' OR 1=1 --"],
    ):
        for kinds in (
            None,
            [],
            ["doc"],
            ["thread"],
            ["section"],
            ["doc", "thread"],
            ["' OR 1=1 --"],
        ):
            for lane in ("fts_raw", "fts_card", "fts_rare"):
                hits = search(
                    database, "needle", sources=source, kinds=kinds, lane=lane, rare_idf=0
                )
                assert all(source is None or hit.source in source for hit in hits)
                assert all(kinds is None or hit.kind in kinds for hit in hits)
                assert all(hit.lane == lane for hit in hits)
