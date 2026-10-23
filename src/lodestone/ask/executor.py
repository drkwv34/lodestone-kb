# SPDX-License-Identifier: Apache-2.0
"""Fan-out allow-listed retrieval calls and normalise evidence (FR-053)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from lodestone.fusion.packet import Evidence

Dispatcher = Callable[[str, dict[str, Any]], Any]


@dataclass
class EvidenceItem:
    label: str
    record_id: int
    score: float
    source: str
    kind: str
    title: str
    uri: str
    snippet: str
    updated_at: str
    packet: dict[str, Any] = field(default_factory=dict)


def _packet(value: object) -> dict[str, Any]:
    if isinstance(value, Evidence):
        return value.model_dump(by_alias=True)
    if isinstance(value, dict):
        return dict(value)
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        payload = dump(by_alias=True)
        if isinstance(payload, dict):
            return payload
    return {
        "schema": "evidence.v1",
        "id": int(getattr(value, "id", 0) or 0),
        "source": str(getattr(value, "source", "") or ""),
        "kind": str(getattr(value, "kind", "") or ""),
        "title": str(getattr(value, "title", "") or ""),
        "uri": str(getattr(value, "uri", "") or ""),
        "snippet": str(getattr(value, "snippet", "") or ""),
        "score": float(getattr(value, "score", 0) or 0),
        "lanes": {},
        "updated_at": str(getattr(value, "updated_at", "") or ""),
        "authors": [],
        "children": [],
        "neighbours": [],
    }


def _item_from_packet(packet: dict[str, Any]) -> EvidenceItem:
    return EvidenceItem(
        label="",
        record_id=int(packet.get("id") or 0),
        score=float(packet.get("score") or 0),
        source=str(packet.get("source") or ""),
        kind=str(packet.get("kind") or ""),
        title=str(packet.get("title") or ""),
        uri=str(packet.get("uri") or ""),
        snippet=str(packet.get("snippet") or ""),
        updated_at=str(packet.get("updated_at") or ""),
        packet=packet,
    )


def _from_hits(hits: list[Any]) -> list[EvidenceItem]:
    return [_item_from_packet(_packet(hit)) for hit in hits]


def _from_matches(matches: list[Any]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for match in matches:
        if isinstance(match, dict):
            record_id = int(match.get("record_id") or 0)
            uri = str(match.get("uri") or "")
            text = str(match.get("text") or "")
        else:
            record_id = int(getattr(match, "record_id", 0) or 0)
            uri = str(getattr(match, "uri", "") or "")
            text = str(getattr(match, "text", "") or "")
        items.append(
            _item_from_packet(
                {
                    "schema": "evidence.v1",
                    "id": record_id,
                    "source": "",
                    "kind": "grep",
                    "title": "",
                    "uri": uri,
                    "snippet": text,
                    "score": 1.0,
                    "lanes": {"grep": {"rank": 1}},
                    "updated_at": "",
                    "authors": [],
                    "children": [],
                    "neighbours": [],
                }
            )
        )
    return items


def _from_people(people: list[Any]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for person in people:
        author = str(getattr(person, "author", "") or "")
        score = float(getattr(person, "score", 0) or 0)
        records = list(getattr(person, "records", []) or [])
        for record_id in records[:3]:
            ident = int(record_id)
            items.append(
                _item_from_packet(
                    {
                        "schema": "evidence.v1",
                        "id": ident,
                        "source": "",
                        "kind": "author",
                        "title": author,
                        "uri": "",
                        "snippet": f"{author} mentioned in record {ident}",
                        "score": score,
                        "lanes": {"who_knows": {"rank": 1}},
                        "updated_at": "",
                        "authors": [author],
                        "children": [],
                        "neighbours": [],
                    }
                )
            )
    return items


def collect_items(result: Any) -> list[EvidenceItem]:
    hits = getattr(result, "hits", None)
    if isinstance(hits, list):
        return _from_hits(hits)
    matches = getattr(result, "matches", None)
    if isinstance(matches, list):
        return _from_matches(matches)
    if isinstance(result, list) and result:
        first = result[0]
        if hasattr(first, "author") and hasattr(first, "records"):
            return _from_people(result)
        return _from_hits(result)
    if isinstance(result, list):
        return []
    return []


def dispatch_call(tool: str, args: dict[str, Any], handler: Dispatcher) -> list[EvidenceItem]:
    try:
        return collect_items(handler(tool, args))
    except (TypeError, ValueError, KeyError):
        return []


def execute_calls(calls: list[dict[str, Any]], handler: Dispatcher) -> list[EvidenceItem]:
    if not calls:
        return []

    async def _fanout() -> list[EvidenceItem]:
        tasks = [
            asyncio.to_thread(
                dispatch_call, str(call["tool"]), dict(call.get("args") or {}), handler
            )
            for call in calls
        ]
        batches = await asyncio.gather(*tasks)
        items: list[EvidenceItem] = []
        for batch in batches:
            items.extend(batch)
        return items

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_fanout())
    collected: list[EvidenceItem] = []
    for call in calls:
        collected.extend(dispatch_call(str(call["tool"]), dict(call.get("args") or {}), handler))
    return collected


def normalise(items: list[EvidenceItem]) -> list[EvidenceItem]:
    best: dict[int, EvidenceItem] = {}
    for item in items:
        if item.record_id <= 0:
            continue
        previous = best.get(item.record_id)
        if previous is None or item.score > previous.score:
            best[item.record_id] = item
    ranked = sorted(best.values(), key=lambda item: (-item.score, item.record_id))
    for index, item in enumerate(ranked, start=1):
        item.label = f"E{index}"
    return ranked
