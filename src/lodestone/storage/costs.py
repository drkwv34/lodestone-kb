# SPDX-License-Identifier: Apache-2.0
"""LLM call log writes and priced per-operation summaries."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from lodestone.config import Prices


def log_call(
    connection: sqlite3.Connection,
    *,
    op: str,
    model: str,
    in_tokens: int,
    out_tokens: int,
    latency_ms: int,
    ok: bool,
) -> None:
    connection.execute(
        "INSERT INTO llm_log(op,model,in_tokens,out_tokens,latency_ms,ok,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (op, model, in_tokens, out_tokens, latency_ms, int(ok), datetime.now(UTC).isoformat()),
    )


def usd(in_tokens: int, out_tokens: int, prices: Prices) -> float:
    return (in_tokens * prices.input + out_tokens * prices.output) / 1_000_000


def summarise(connection: sqlite3.Connection, prices: Prices) -> dict[str, object]:
    operations: list[dict[str, object]] = []
    totals = {
        "calls": 0,
        "in_tokens": 0,
        "out_tokens": 0,
        "ok": 0,
        "latency_ms": 0,
        "usd": 0.0,
    }
    rows = connection.execute(
        "SELECT op, count(*), coalesce(sum(in_tokens),0), coalesce(sum(out_tokens),0), "
        "coalesce(sum(ok),0), coalesce(sum(latency_ms),0) FROM llm_log GROUP BY op ORDER BY op"
    )
    for op, calls, inbound, outbound, ok, latency in rows:
        cost = usd(int(inbound), int(outbound), prices)
        operations.append(
            {
                "op": op,
                "calls": int(calls),
                "in_tokens": int(inbound),
                "out_tokens": int(outbound),
                "ok": int(ok),
                "latency_ms": int(latency),
                "usd": cost,
            }
        )
        totals["calls"] += int(calls)
        totals["in_tokens"] += int(inbound)
        totals["out_tokens"] += int(outbound)
        totals["ok"] += int(ok)
        totals["latency_ms"] += int(latency)
        totals["usd"] = float(totals["usd"]) + cost
    totals["usd"] = float(totals["usd"])
    return {"operations": operations, "total": totals, "prices": prices.model_dump(mode="json")}
