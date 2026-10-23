# SPDX-License-Identifier: Apache-2.0
"""Read a stored record together with its card and raw text."""

from __future__ import annotations

import json
import sqlite3


def get_record(
    connection: sqlite3.Connection, ref: str | int, source: str | None = None
) -> dict[str, object]:
    where = ["r.tombstoned=0"]
    parameters: list[str | int] = []
    if isinstance(ref, int) or str(ref).isdigit():
        where.append("r.id=?")
        parameters.append(int(ref))
    else:
        where.append("r.ext_id=?")
        parameters.append(str(ref))
        if source is not None:
            where.append("s.name=?")
            parameters.append(source)
    sql = (
        "SELECT r.id,r.ext_id,s.name,r.kind,r.title,r.text,r.card_json,r.card_method,"
        "r.norm_text,r.context_prefix,r.metadata_json FROM records r "
        "JOIN sources s ON s.id=r.source_id WHERE "
    )
    row = connection.execute(sql + " AND ".join(where) + " LIMIT 1", parameters).fetchone()
    if row is None:
        raise KeyError(f"record not found: {ref}")
    card = json.loads(row[6]) if row[6] else None
    children = [
        {
            "id": int(child[0]),
            "kind": str(child[1] or ""),
            "title": str(child[2] or ""),
            "snippet": str(child[3] or "").replace("\n", " ")[:240],
        }
        for child in connection.execute(
            "SELECT id, kind, title, substr(text,1,240) FROM records "
            "WHERE parent_id=? AND tombstoned=0 ORDER BY seq, id",
            (row[0],),
        )
    ]
    return {
        "id": row[0],
        "ext_id": row[1],
        "source": row[2],
        "kind": row[3],
        "title": row[4],
        "raw_text": row[5],
        "card": card,
        "card_method": row[7],
        "norm_text": row[8],
        "context_prefix": row[9],
        "metadata": json.loads(row[10]),
        "children": children,
    }
