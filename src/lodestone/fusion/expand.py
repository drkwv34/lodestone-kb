# SPDX-License-Identifier: Apache-2.0
"""Attach previous and next siblings for chunk and section hits."""

from __future__ import annotations

import sqlite3
from typing import Any

EXPAND_KINDS = {"section", "code", "burst"}


def neighbours(
    connection: sqlite3.Connection,
    record_id: int,
    *,
    n: int = 1,
    max_chars: int = 4000,
) -> list[dict[str, Any]]:
    if n < 1:
        return []
    row = connection.execute(
        "SELECT parent_id, seq, kind FROM records WHERE id=? AND tombstoned=0",
        (record_id,),
    ).fetchone()
    if row is None or row[0] is None or row[2] not in EXPAND_KINDS:
        return []
    parent_id = int(row[0])
    siblings = list(
        connection.execute(
            "SELECT id, seq, title, text FROM records "
            "WHERE parent_id=? AND tombstoned=0 ORDER BY seq, id",
            (parent_id,),
        )
    )
    index = next((i for i, sibling in enumerate(siblings) if sibling[0] == record_id), None)
    if index is None:
        return []
    lo = max(0, index - n)
    hi = min(len(siblings), index + n + 1)
    attached: list[dict[str, Any]] = []
    used = 0
    for sibling in siblings[lo:hi]:
        ident, sibling_seq, title, text = sibling
        snippet = str(text or "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(snippet) > remaining:
            snippet = snippet[:remaining]
        attached.append(
            {
                "id": int(ident),
                "seq": int(sibling_seq),
                "title": str(title or ""),
                "snippet": snippet,
            }
        )
        used += len(snippet)
    return attached
