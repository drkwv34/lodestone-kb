# SPDX-License-Identifier: Apache-2.0
"""Shared retrieval filters applied before lane scoring and fusion."""

from __future__ import annotations

import re
from dataclasses import dataclass

KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Scope:
    sources: list[str] | None = None
    kinds: list[str] | None = None
    authors: list[str] | None = None
    since: str | None = None
    until: str | None = None
    metadata: dict[str, str] | None = None


def parse_metadata(pairs: list[str] | None) -> dict[str, str] | None:
    if pairs is None:
        return None
    parsed: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError("metadata filters must be key=value")
        key, value = item.split("=", 1)
        if not KEY.fullmatch(key):
            raise ValueError("metadata keys must be identifiers")
        parsed[key] = value
    return parsed


def clauses(
    scope: Scope, *, record: str = "r", source: str = "s"
) -> tuple[list[str], list[object]]:
    where: list[str] = [f"{record}.tombstoned=0"]
    parameters: list[object] = []
    mapping = (
        (f"{source}.name", scope.sources),
        (f"{record}.kind", scope.kinds),
    )
    for column, values in mapping:
        if values is None:
            continue
        if not values:
            return ["1=0"], []
        where.append(column + " IN (" + ",".join("?" for _ in values) + ")")
        parameters.extend(values)
    if scope.authors is not None:
        if not scope.authors:
            return ["1=0"], []
        placeholders = ",".join("?" for _ in scope.authors)
        where.append(
            "("  # noqa: S608
            + record
            + ".author IN ("
            + placeholders
            + ") OR EXISTS (SELECT 1 FROM json_each(COALESCE("
            + record
            + ".authors_json, '[]')) WHERE json_each.value IN ("
            + placeholders
            + ")))"
        )
        parameters.extend(scope.authors)
        parameters.extend(scope.authors)
    if scope.since:
        where.append(f"{record}.updated_at >= ?")
        parameters.append(scope.since)
    if scope.until:
        until = scope.until
        if len(until) == 10:
            until = until + "T23:59:59.999999Z"
        where.append(f"{record}.updated_at <= ?")
        parameters.append(until)
    if scope.metadata is not None:
        if not scope.metadata:
            return ["1=0"], []
        for key, value in scope.metadata.items():
            if not KEY.fullmatch(key):
                raise ValueError("metadata keys must be identifiers")
            where.append(f"CAST(json_extract({record}.metadata_json, ?) AS TEXT) = ?")
            parameters.extend(["$." + key, value])
    return where, parameters
