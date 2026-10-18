# SPDX-License-Identifier: Apache-2.0
"""Validated retrieval card shape used for LLM output, cache and storage."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CharSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class Card(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question: str = Field(max_length=200)
    summary: str = Field(max_length=500)
    resolution: str = Field(default="", max_length=500)
    entities: list[str] = Field(default_factory=list, max_length=8)
    code_refs: list[str] = Field(default_factory=list, max_length=12)
    source_message_ids: list[str] = Field(default_factory=list)
    char_spans: list[CharSpan] = Field(default_factory=list)
