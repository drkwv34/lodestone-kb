# SPDX-License-Identifier: Apache-2.0
"""Versioned evidence.v1 packets for fused search hits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceChild(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    kind: str = ""
    snippet: str = ""
    title: str = ""


class EvidenceNeighbour(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    seq: int = 0
    title: str = ""
    snippet: str = ""


class LaneExplain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rank: int
    raw_score: float = 0
    contribution: float = 0
    score: float | None = None


class Explain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lanes: dict[str, LaneExplain] = Field(default_factory=dict)
    rrf: float = 0
    decay_factor: float = 1
    rerank_score: float | None = None
    final: float = 0


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schema_name: str = Field(default="evidence.v1", alias="schema")
    id: int
    source: str
    kind: str
    title: str
    uri: str = ""
    snippet: str = ""
    text: str | None = None
    score: float
    lanes: dict[str, LaneExplain] = Field(default_factory=dict)
    updated_at: str
    authors: list[str] = Field(default_factory=list)
    card: dict[str, Any] | None = None
    children: list[EvidenceChild] = Field(default_factory=list)
    neighbours: list[EvidenceNeighbour] = Field(default_factory=list)
    explain: Explain | None = None


def evidence_schema_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "schemas" / "evidence.v1.json",
        here.parents[1] / "schemas" / "evidence.v1.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("schemas/evidence.v1.json")


def evidence_schema() -> dict[str, Any]:
    payload: object = json.loads(evidence_schema_path().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence schema must be an object")
    return payload


def validate_packet(packet: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    spec = schema or evidence_schema()
    required = spec.get("required", [])
    properties = spec.get("properties", {})
    for key in required:
        if key not in packet:
            raise ValueError(f"evidence.v1 missing {key}")
    if spec.get("additionalProperties") is False:
        extra = set(packet) - set(properties)
        if extra:
            raise ValueError(f"evidence.v1 extra fields: {sorted(extra)}")
    if packet.get("schema") != "evidence.v1":
        raise ValueError("schema must be evidence.v1")


def packet_from_row(
    row: dict[str, Any],
    *,
    score: float,
    lanes: dict[str, LaneExplain],
    children: list[EvidenceChild] | None = None,
    neighbours: list[EvidenceNeighbour] | None = None,
    explain: Explain | None = None,
    include_text: bool = False,
) -> Evidence:
    authors = list(row.get("authors") or [])
    author = row.get("author")
    if author and author not in authors:
        authors.insert(0, str(author))
    card = row.get("card")
    return Evidence(
        schema="evidence.v1",
        id=int(row["id"]),
        source=str(row["source"]),
        kind=str(row["kind"]),
        title=str(row.get("title") or ""),
        uri=str(row.get("uri") or ""),
        snippet=str(row.get("snippet") or ""),
        text=str(row["text"]) if include_text and row.get("text") is not None else None,
        score=score,
        lanes=lanes,
        updated_at=str(row.get("updated_at") or ""),
        authors=authors,
        card=card if isinstance(card, dict) else None,
        children=children or [],
        neighbours=neighbours or [],
        explain=explain,
    )
