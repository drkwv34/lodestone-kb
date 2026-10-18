# SPDX-License-Identifier: Apache-2.0
import sqlite3

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from lodestone.config import Prices
from lodestone.storage.costs import log_call, summarise, usd


@given(
    st.lists(
        st.tuples(
            st.sampled_from(["card", "embed", "context"]),
            st.integers(min_value=0, max_value=10_000),
            st.integers(min_value=0, max_value=10_000),
            st.integers(min_value=0, max_value=5_000),
            st.booleans(),
        ),
        max_size=25,
    )
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fr_026_cost_totals_equal_sum_of_log_rows(
    database: sqlite3.Connection,
    rows: list[tuple[str, int, int, int, bool]],
) -> None:
    database.execute("DELETE FROM llm_log")
    prices = Prices(input=1.25, output=5.5)
    inbound = outbound = calls = ok_count = latency = 0
    for op, in_tokens, out_tokens, latency_ms, ok in rows:
        log_call(
            database,
            op=op,
            model="m",
            in_tokens=in_tokens,
            out_tokens=out_tokens,
            latency_ms=latency_ms,
            ok=ok,
        )
        inbound += in_tokens
        outbound += out_tokens
        calls += 1
        ok_count += int(ok)
        latency += latency_ms
    database.commit()
    summary = summarise(database, prices)
    total = summary["total"]
    assert isinstance(total, dict)
    assert total["calls"] == calls
    assert total["in_tokens"] == inbound
    assert total["out_tokens"] == outbound
    assert total["ok"] == ok_count
    assert total["latency_ms"] == latency
    assert total["usd"] == pytest.approx(usd(inbound, outbound, prices))
    by_op = {row["op"]: row for row in summary["operations"]}  # type: ignore[union-attr]
    for op in {item[0] for item in rows}:
        group = [item for item in rows if item[0] == op]
        assert by_op[op]["calls"] == len(group)
        assert by_op[op]["in_tokens"] == sum(item[1] for item in group)
        assert by_op[op]["usd"] == pytest.approx(
            usd(sum(item[1] for item in group), sum(item[2] for item in group), prices)
        )
