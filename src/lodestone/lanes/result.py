# SPDX-License-Identifier: Apache-2.0
"""Search hits plus skip notices for optional lanes."""

from __future__ import annotations

from dataclasses import dataclass, field

from lodestone.lanes.fts import Hit


@dataclass
class SearchResult:
    hits: list[Hit]
    notices: list[str] = field(default_factory=list)
    lane: str = ""
    packets: list[dict[str, object]] = field(default_factory=list)
