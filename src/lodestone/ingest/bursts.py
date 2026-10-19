# SPDX-License-Identifier: Apache-2.0
"""Same-author burst grouping and the FR-013 weighted scoring gate."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from lodestone.config import Bursts
from lodestone.connectors.files import Message
from lodestone.connectors.threads import render_transcript
from lodestone.tokenize import tokenize


@dataclass(frozen=True)
class Burst:
    group: int
    author: str
    messages: tuple[Message, ...]
    body: str
    text: str
    reactions: int

    @property
    def chars(self) -> int:
        return len(self.body)


def group_bursts(messages: Sequence[Message]) -> list[Burst]:
    groups: list[list[Message]] = []
    for message in messages:
        if groups and groups[-1][-1].author == message.author:
            groups[-1].append(message)
        else:
            groups.append([message])
    bursts: list[Burst] = []
    for index, group in enumerate(groups):
        packed = tuple(group)
        body = "\n".join(item.text for item in packed)
        bursts.append(
            Burst(
                group=index,
                author=packed[0].author,
                messages=packed,
                body=body,
                text=render_transcript(packed),
                reactions=sum(item.reactions for item in packed),
            )
        )
    return bursts


def burst_score(
    body: str,
    reactions: int,
    config: Bursts,
    idf_of: Callable[[str], float],
) -> float:
    tokens = tokenize(body)
    max_idf = max((idf_of(token) for token in tokens), default=0.0)
    return (
        config.w_idf * float(max_idf >= config.idf_min)
        + config.w_len * float(len(body) >= config.min_chars)
        + config.w_react * float(reactions >= 1)
    )


def keep_burst(burst: Burst, config: Bursts, idf_of: Callable[[str], float]) -> bool:
    return burst_score(burst.body, burst.reactions, config, idf_of) >= config.threshold


def qualifying_bursts(
    messages: Sequence[Message], config: Bursts, idf_of: Callable[[str], float]
) -> list[Burst]:
    return [burst for burst in group_bursts(messages) if keep_burst(burst, config, idf_of)]
