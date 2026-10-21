# SPDX-License-Identifier: Apache-2.0
"""Literal and regex scan over raw record text with a catastrophic-pattern guard."""

from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import time

from lodestone.lanes.fts import Hit
from lodestone.lanes.result import SearchResult
from lodestone.lanes.scope import Scope, clauses

MAX_PATTERN = 500
TIMEOUT_S = 2.0
NESTED_QUANTIFIER = re.compile(r"\([^)]*[+*][^)]*\)[+*?]")
STACKED_QUANTIFIER = re.compile(r"[+*][?+]|\+\+|\*\*")


class GrepError(ValueError):
    """Rejected or invalid grep pattern."""


def pathological(pattern: str) -> bool:
    return bool(NESTED_QUANTIFIER.search(pattern) or STACKED_QUANTIFIER.search(pattern))


def compile_pattern(pattern: str, *, regex: bool) -> re.Pattern[str]:
    if len(pattern) > MAX_PATTERN:
        raise GrepError("pattern length exceeds 500")
    source = pattern if regex else re.escape(pattern)
    if regex and pathological(source):
        raise GrepError("pathological regex rejected")
    try:
        return re.compile(source)
    except re.error as exc:
        raise GrepError(f"invalid regex: {exc}") from None


def _snippet(lines: list[str], index: int, context: int) -> str:
    lo = max(0, index - context)
    hi = min(len(lines), index + context + 1)
    parts = [f"{number + 1}: {lines[number]}" for number in range(lo, hi)]
    return "\n".join(parts)


def search(
    connection: sqlite3.Connection,
    pattern: str,
    *,
    regex: bool = False,
    scope: Scope | None = None,
    limit: int = 10,
    context: int = 2,
    timeout_s: float = TIMEOUT_S,
) -> SearchResult:
    if limit < 1:
        raise ValueError("limit must be positive")
    compiled = compile_pattern(pattern, regex=regex)

    def regexp(value: str | None, text: str | None) -> int:
        return 1 if compiled.search(text or "") else 0

        with contextlib.suppress(sqlite3.OperationalError):
            connection.create_function("REGEXP", 2, regexp)

    where, parameters = clauses(scope or Scope())
    sql = (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.metadata_json,r.text,r.updated_at "
        "FROM records r JOIN sources s ON s.id=r.source_id WHERE " + " AND ".join(where)
    )
    deadline = time.monotonic() + timeout_s
    hits: list[Hit] = []
    notices: list[str] = []
    for row in connection.execute(sql, parameters):
        if time.monotonic() > deadline:
            notices.append("GrepTimeout")
            break
        text = str(row[6] or "")
        lines = text.splitlines() or [text]
        matches = [index for index, line in enumerate(lines) if compiled.search(line)]
        if not matches:
            continue
        first = matches[0]
        hits.append(
            Hit(
                id=int(row[0]),
                ext_id=str(row[1]),
                source=str(row[2]),
                kind=str(row[3]),
                title=str(row[4] or ""),
                uri=str(json.loads(row[5] or "{}").get("uri", "")),
                snippet=_snippet(lines, first, context),
                score=float(len(matches)),
                lane="grep",
                updated_at=str(row[7] or ""),
            )
        )
        if len(hits) >= limit:
            break
    hits.sort(key=lambda hit: (-hit.score, hit.updated_at, -hit.id))
    return SearchResult(hits[:limit], notices, "grep")
