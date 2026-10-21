# SPDX-License-Identifier: Apache-2.0
import pytest

from lodestone.lanes.grep import GrepError, compile_pattern, pathological, search


def test_fr_034_grep_lane_and_regex_guard(database, record_factory) -> None:
    record_factory("alpha\nERR_MANIFEST_TIMEOUT on line two\nomega", ext_id="manifest.md")
    hits = search(database, r"ERR_[A-Z_]+", regex=True, limit=5, context=1).hits
    assert hits
    assert hits[0].lane == "grep"
    assert "2: ERR_MANIFEST_TIMEOUT on line two" in hits[0].snippet
    assert "1: alpha" in hits[0].snippet
    literal = search(database, "ERR_MANIFEST_TIMEOUT", regex=False).hits
    assert literal[0].id == hits[0].id
    with pytest.raises(GrepError, match="pathological"):
        compile_pattern("(a+)+", regex=True)
    with pytest.raises(GrepError, match="pathological"):
        search(database, "(x+)+y", regex=True)
    with pytest.raises(GrepError, match="500"):
        search(database, "a" * 501, regex=True)
    with pytest.raises(GrepError, match="invalid"):
        search(database, "(", regex=True)
    assert pathological("(a*)*")
    timed = search(database, "alpha", regex=False, timeout_s=0)
    assert "GrepTimeout" in timed.notices
    with pytest.raises(ValueError, match="limit"):
        search(database, "alpha", limit=0)
