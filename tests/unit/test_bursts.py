# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime

import pytest

from lodestone.config import Bursts
from lodestone.connectors.files import Message
from lodestone.ingest.bursts import burst_score, group_bursts, keep_burst, qualifying_bursts

TS = datetime(2026, 7, 1, 9, 14, tzinfo=UTC)
DETAIL = (
    "Checkpoint restore stalls on the NFS mount after the manifest load. "
    "The prefetch window stays full so the loader waits on file handles. "
    "CKPT_PREFETCH needs to drop; the default is too high for this filesystem. "
    "ERR_MANIFEST_TIMEOUT shows up in the client log when the wait exceeds the cap."
)
RESOLUTION = "Setting CKPT_PREFETCH=4 makes the restore complete on NFS."
CEREBRAS = [
    Message("m1", "author_a", TS, "sounds good", 0),
    Message("m2", "author_a", TS, "thanks", 0),
    Message("m3", "author_b", TS, DETAIL, 0),
    Message("m4", "author_b", TS, RESOLUTION, 3),
    Message("m5", "author_c", TS, "ack", 0),
]


def figure_idf(term: str) -> float:
    rare = {"ckpt_prefetch", "err_manifest_timeout", "nfs"}
    return 5.0 if term in rare else 0.1


@pytest.mark.parametrize(
    ("config", "kept_authors"),
    [
        (Bursts(), ["author_b"]),
        (
            Bursts(min_chars=1, w_idf=0, w_react=0, threshold=1),
            ["author_a", "author_b", "author_c"],
        ),
        (Bursts(min_chars=10000, w_idf=0, w_react=0), []),
        (Bursts(threshold=3), ["author_b"]),
        (Bursts(threshold=3, w_idf=0), []),
    ],
)
def test_fr_013_cerebras_five_message_figure(config: Bursts, kept_authors: list[str]) -> None:
    bursts = group_bursts(CEREBRAS)
    assert [burst.author for burst in bursts] == ["author_a", "author_b", "author_c"]
    assert bursts[0].chars < 200 and bursts[0].reactions == 0
    assert bursts[1].chars >= 200 and bursts[1].reactions >= 1
    short = burst_score(bursts[0].body, bursts[0].reactions, Bursts(), figure_idf)
    long = burst_score(bursts[1].body, bursts[1].reactions, Bursts(), figure_idf)
    assert short < 1.0
    assert long >= 1.0
    kept = [burst.author for burst in qualifying_bursts(CEREBRAS, config, figure_idf)]
    assert kept == kept_authors
    assert keep_burst(bursts[1], Bursts(), figure_idf) is True
    assert keep_burst(bursts[0], Bursts(), figure_idf) is False
