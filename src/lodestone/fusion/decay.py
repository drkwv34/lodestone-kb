# SPDX-License-Identifier: Apache-2.0
"""Post-fusion recency decay with a per-kind floor."""

from __future__ import annotations

from datetime import UTC, datetime

from lodestone.config import Decay, Kind

KIND_DECAY: dict[str, Kind] = {
    "thread": "thread",
    "burst": "thread",
    "doc": "doc",
    "section": "doc",
    "code_file": "code",
    "code": "code",
}


def parse_stamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        stamp = value
    else:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp.astimezone(UTC)


def age_days(updated_at: str | datetime, now: datetime | None = None) -> float:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    delta = (current.astimezone(UTC) - parse_stamp(updated_at)).total_seconds() / 86400
    return max(0.0, delta)


def decay_factor(age: float, half_life_days: float, floor: float) -> float:
    if half_life_days <= 0:
        return 1.0
    return float(max(floor, 0.5 ** (age / half_life_days)))


def config_decay(kind: str, table: dict[Kind, Decay]) -> Decay:
    key = KIND_DECAY.get(kind, "doc")
    if kind in table:
        return table[kind]
    if key in table:
        return table[key]
    return Decay()


def apply_decay(
    score: float,
    updated_at: str,
    *,
    kind: str,
    table: dict[Kind, Decay],
    now: datetime | None = None,
    enabled: bool = True,
) -> tuple[float, float]:
    if not enabled:
        return score, 1.0
    settings = config_decay(kind, table)
    factor = decay_factor(age_days(updated_at, now), settings.half_life_days, settings.floor)
    return score * factor, factor
