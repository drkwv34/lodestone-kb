# SPDX-License-Identifier: Apache-2.0
"""Markdown headings, paragraph boundaries and fenced code without altering source text."""

from __future__ import annotations

import re

from lodestone.chunking import Chunk, pack
from lodestone.config import Chunks

VERSION = "markdown-v1"
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")


def chunk(text: str, title: str = "", config: Chunks | None = None) -> list[Chunk]:
    cfg = config or Chunks()
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    headings: list[tuple[int, int, str]] = []
    paragraphs = {0, len(text)}
    fence = ""
    fence_size = 0
    index = 0
    while index < len(lines):
        line = lines[index].rstrip("\r\n")
        marker = FENCE.match(line)
        if fence:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence) + "{" + str(fence_size) + r",}[ \t]*", line
            ):
                paragraphs.add(offsets[index + 1])
                fence = ""
        elif marker and not (marker[1][0] == "`" and "`" in marker[2]):
            paragraphs.add(offsets[index])
            fence, fence_size = marker[1][0], len(marker[1])
        else:
            heading = HEADING.match(line)
            if heading:
                headings.append((offsets[index], len(heading[1]), heading[2].strip()))
            elif (
                line.strip()
                and index + 1 < len(lines)
                and (underline := SETEXT.match(lines[index + 1].rstrip("\r\n")))
            ):
                headings.append((offsets[index], 1 if underline[1][0] == "=" else 2, line.strip()))
                index += 1
            elif not line.strip():
                paragraphs.add(offsets[index + 1])
        index += 1
    sections: list[tuple[int, str]] = []
    path: list[tuple[int, str]] = []
    if not headings or headings[0][0] > 0:
        sections.append((0, title))
    for offset, depth, heading_title in headings:
        while path and path[-1][0] >= depth:
            path.pop()
        path.append((depth, heading_title))
        sections.append((offset, " > ".join(part for _, part in path)))
    result: list[Chunk] = []
    for number, (start, heading_path) in enumerate(sections):
        end = sections[number + 1][0] if number + 1 < len(sections) else len(text)
        boundaries = [start, *sorted(point for point in paragraphs if start < point < end), end]
        result.extend(
            Chunk(heading_path, text[left:right], left, right)
            for left, right in pack(text, boundaries, cfg)
        )
    return result
