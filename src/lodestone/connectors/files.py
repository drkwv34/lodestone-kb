# SPDX-License-Identifier: Apache-2.0
"""Bounded UTF-8 file discovery inside a resolved source root."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

from pathspec import GitIgnoreSpec

from lodestone.config import Source

LOGGER = logging.getLogger(__name__)
SUPPORTED = {".md", ".txt", ".rst"}
MAX_IGNORE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class RawItem:
    ext_id: str
    kind_hint: str
    title: str
    text: str
    metadata: dict[str, str]
    updated_at: datetime


@dataclass(frozen=True)
class Skip:
    path: str
    reason: str


def jailed_path(root: Path, relative: str) -> Path:
    """Reject absolute paths, traversal and links resolving outside the root."""
    path = PurePosixPath(relative.replace("\\", "/"))
    windows = PureWindowsPath(relative)
    if path.is_absolute() or windows.drive or ".." in path.parts:
        raise ValueError("path traversal or absolute path")
    resolved_root = root.resolve(strict=True)
    resolved = (resolved_root / relative).resolve(strict=True)
    if not resolved.is_relative_to(resolved_root):
        raise ValueError("symlink escapes source root")
    return resolved


def validate_patterns(patterns: list[str]) -> None:
    for pattern in patterns:
        path = PurePosixPath(pattern.replace("\\", "/"))
        if path.is_absolute() or PureWindowsPath(pattern).drive or ".." in path.parts:
            raise ValueError("include/exclude patterns must stay inside the source root")


class FilesConnector:
    def __init__(self) -> None:
        self.skipped: list[Skip] = []

    def skip(self, path: str, reason: str) -> None:
        self.skipped.append(Skip(path, reason))
        LOGGER.warning("Skipping %s: %s", path, reason)

    def discover(self, cfg: Source) -> Iterator[RawItem]:
        validate_patterns(cfg.include + cfg.exclude)
        root = cfg.path.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("files source path must be a directory")
        self.skipped.clear()
        include = GitIgnoreSpec.from_lines(cfg.include)
        exclude = GitIgnoreSpec.from_lines(cfg.exclude)
        rules: dict[Path, list[tuple[Path, GitIgnoreSpec]]] = {}
        for directory, dirs, files in os.walk(root, followlinks=False):
            current = Path(directory)
            inherited = rules.get(current.parent, [])
            local = list(inherited)
            ignore = current / ".gitignore"
            if ignore.exists():
                try:
                    safe = jailed_path(root, ignore.relative_to(root).as_posix())
                    with safe.open("rb") as stream:
                        data = stream.read(MAX_IGNORE_BYTES + 1)
                    if len(data) > MAX_IGNORE_BYTES:
                        raise ValueError("gitignore exceeds 1 MiB")
                    local.append(
                        (current, GitIgnoreSpec.from_lines(data.decode("utf-8").splitlines()))
                    )
                except (OSError, UnicodeError, ValueError) as exc:
                    self.skip(ignore.relative_to(root).as_posix(), str(exc))
                    dirs.clear()
                    continue
            rules[current] = local
            for name in sorted(dirs):
                path = current / name
                relative = path.relative_to(root).as_posix()
                if path.is_symlink() or name == ".git" or self.ignored(path, local, directory=True):
                    dirs.remove(name)
                    self.skip(relative, "symlink directory or gitignored")
            dirs.sort()
            for name in sorted(files):
                path = current / name
                relative = path.relative_to(root).as_posix()
                if name == ".gitignore":
                    continue
                if self.ignored(path, local) or exclude.match_file(relative):
                    self.skip(relative, "ignored")
                    continue
                if cfg.include and not include.match_file(relative):
                    self.skip(relative, "not included")
                    continue
                if path.suffix.lower() not in SUPPORTED:
                    self.skip(relative, "unsupported extension (Day 2: md/txt/rst)")
                    continue
                item = self.read(root, relative, cfg.max_file_bytes)
                if item is not None:
                    yield item

    @staticmethod
    def ignored(
        path: Path, rules: list[tuple[Path, GitIgnoreSpec]], *, directory: bool = False
    ) -> bool:
        ignored = False
        for base, spec in rules:
            decision = spec.check_file(
                path.relative_to(base).as_posix() + ("/" if directory else "")
            )
            if decision.include is not None:
                ignored = decision.include
        return ignored

    def read(self, root: Path, relative: str, max_bytes: int) -> RawItem | None:
        try:
            safe = jailed_path(root, relative)
            if not safe.is_file():
                self.skip(relative, "not a regular file")
                return None
            stat = safe.stat()
            if stat.st_size > max_bytes:
                self.skip(relative, "oversize")
                return None
            with safe.open("rb") as stream:
                data = stream.read(max_bytes + 1)
            if len(data) > max_bytes:
                self.skip(relative, "oversize")
                return None
            if any((byte < 32 and byte not in (9, 10, 12, 13)) or byte == 127 for byte in data):
                self.skip(relative, "binary")
                return None
            text = data.decode("utf-8")
            return RawItem(
                ext_id=relative,
                kind_hint=safe.suffix.lower()[1:],
                title=Path(relative).stem,
                text=text,
                metadata={"path": relative, "uri": safe.as_uri()},
                updated_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            )
        except UnicodeError:
            self.skip(relative, "binary or invalid UTF-8")
        except (OSError, ValueError) as exc:
            self.skip(relative, str(exc))
        return None
