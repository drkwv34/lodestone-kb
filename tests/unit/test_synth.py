# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from lodestone.bench.evalset import CATEGORIES, load_evalset
from lodestone.bench.synth import generate

PINNED_SEED = 1
PINNED_THREADS = 6
PINNED_HASH = "0f3dc6b327bba3e644f746002dbea157b1a61bc922b6f475059e46d2d3b129c1"


def test_fr_071_synth_determinism(tmp_path: Path) -> None:
    first = generate(tmp_path / "a", seed=PINNED_SEED, threads=PINNED_THREADS)
    second = generate(tmp_path / "b", seed=PINNED_SEED, threads=PINNED_THREADS)
    assert first.corpus_hash == second.corpus_hash
    left = sorted(
        (path.relative_to(tmp_path / "a").as_posix(), path.read_bytes())
        for path in (tmp_path / "a").rglob("*")
        if path.is_file()
    )
    right = sorted(
        (path.relative_to(tmp_path / "b").as_posix(), path.read_bytes())
        for path in (tmp_path / "b").rglob("*")
        if path.is_file()
    )
    assert left == right
    other = generate(tmp_path / "c", seed=PINNED_SEED + 1, threads=PINNED_THREADS)
    assert other.corpus_hash != first.corpus_hash
    assert first.corpus_hash == PINNED_HASH


def test_fr_071_synth_categories(tmp_path: Path) -> None:
    result = generate(tmp_path / "synth", seed=1, threads=6)
    rows = load_evalset(result.evalset)
    found = {row.category for row in rows}
    assert found == set(CATEGORIES)
    assert (tmp_path / "synth" / "threads.jsonl").is_file()
    assert list((tmp_path / "synth" / "docs").glob("*.md"))
    with pytest.raises(ValueError, match="threads"):
        generate(tmp_path / "zero", seed=1, threads=0)
