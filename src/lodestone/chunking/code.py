# SPDX-License-Identifier: Apache-2.0
"""Regex class/struct, function/method and block discovery for common code languages.

This deliberately coarse parser masks comments and strings before matching; it is
not a compiler. Unrecognised syntax still produces bounded, lossless chunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise

from lodestone.chunking import Chunk, pack
from lodestone.config import Chunks

VERSION = "code-v1"
CLASS = r"\b(?:class|struct|enum|interface|trait|impl)\s+(\w+)"
C_FUNCTION = (
    r"^\s*(?:(?:[\w*&:<>,\[\]]+)[ \t]+)+([~\w]+)\s*\([^;{}]*\)"
    r"[^;{}]*\{"
)
BLOCK = r"^\s*(?:(?:else\s+)?(?:if|for|while|switch|match|try|catch|with)\b|else\b)"


@dataclass(frozen=True)
class Language:
    classes: str
    functions: str
    blocks: str = BLOCK


LANGUAGES = {
    "py": Language(r"^\s*class\s+(\w+)", r"^\s*(?:async\s+)?def\s+(\w+)\s*\("),
    "js": Language(
        CLASS,
        r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\("
        r"|^\s*(?:(?:static|async|get|set)\s+)*(\w+)\s*\([^;{}]*\)\s*\{"
        r"|^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=.*=>",
    ),
    "ts": Language(
        CLASS,
        r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\("
        r"|^\s*(?:(?:public|private|protected|static|async|readonly)\s+)*"
        r"(\w+)\s*\([^;{}]*\)[^;{}]*\{"
        r"|^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=.*=>",
    ),
    "go": Language(
        r"\btype\s+(\w+)\s+(?:struct|interface)", r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\("
    ),
    "java": Language(CLASS, C_FUNCTION),
    "c": Language(CLASS, C_FUNCTION),
    "cpp": Language(CLASS, C_FUNCTION),
    "rs": Language(CLASS, r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]"),
}


@dataclass(frozen=True)
class Symbol:
    start: int
    end: int
    name: str
    signature: str
    level: int


def masked(text: str) -> str:
    """Keep offsets/newlines while hiding comments and quoted strings."""
    pattern = (
        r"\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|"
        r"/\*[\s\S]*?\*/|//[^\n]*|\#[^\n]*"
    )
    return re.sub(pattern, lambda match: re.sub(r"[^\r\n]", " ", match[0]), text)


def symbols(text: str, language: str) -> list[Symbol]:
    table = LANGUAGES.get(language)
    if table is None:
        return []
    clean = masked(text)
    lines = clean.splitlines(keepends=True)
    originals = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    patterns = [re.compile(value) for value in (table.classes, table.functions, table.blocks)]
    result: list[Symbol] = []
    for index, line in enumerate(lines):
        for level, pattern in enumerate(patterns):
            match = pattern.search(line)
            if not match:
                continue
            name = next((group for group in match.groups() if group), line.strip().split()[0])
            if level == 1 and name in {"if", "for", "while", "switch", "catch", "with", "match"}:
                continue
            start = offsets[index]
            end = len(text)
            if language == "py":
                indent = len(line) - len(line.lstrip())
                for following in range(index + 1, len(lines)):
                    candidate = lines[following]
                    if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= indent:
                        end = offsets[following]
                        break
            else:
                opening = clean.find("{", start)
                if opening < 0:
                    continue
                depth = 1
                cursor = opening + 1
                while cursor < len(clean) and depth:
                    depth += (clean[cursor] == "{") - (clean[cursor] == "}")
                    cursor += 1
                end = cursor
            result.append(Symbol(start, end, name, originals[index].strip(), level))
            break
    return result


def outline(text: str, language: str) -> str:
    return "\n".join(symbol.signature for symbol in symbols(text, language) if symbol.level < 2)


def chunk(text: str, language: str, title: str = "", config: Chunks | None = None) -> list[Chunk]:
    cfg = config or Chunks()
    found = symbols(text, language)
    # Methods are always independent units. Oversized methods refine at block boundaries.
    cuts = {0, len(text)}
    target = cfg.target_tokens * cfg.chars_per_token
    for symbol in found:
        if symbol.level < 2 or any(
            enclosing.level == 1
            and enclosing.start < symbol.start < enclosing.end
            and enclosing.end - enclosing.start > target
            for enclosing in found
        ):
            cuts.add(symbol.start)
    result: list[Chunk] = []
    points = sorted(cuts)
    for start, end in pairwise(points):
        enclosing = [symbol for symbol in found if symbol.start <= start < symbol.end]
        heading = " > ".join([title, *(symbol.name for symbol in enclosing)]).strip(" >")
        boundaries = [start]
        offset = start
        for line in text[start:end].splitlines(keepends=True):
            offset += len(line)
            if not line.strip():
                boundaries.append(offset)
        if boundaries[-1] != end:
            boundaries.append(end)
        result.extend(
            Chunk(heading, text[left:right], left, right)
            for left, right in pack(text, boundaries, cfg)
        )
    return result
