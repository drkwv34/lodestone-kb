# SPDX-License-Identifier: Apache-2.0
"""Check internal markdown links in README and user guides (NFR-016)."""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    ROOT / "README.md",
    ROOT / "docs/quickstart.md",
    ROOT / "docs/concepts.md",
    ROOT / "docs/connectors.md",
    ROOT / "docs/mcp.md",
    ROOT / "docs/bench.md",
    ROOT / "docs/privacy.md",
    ROOT / "docs/faq.md",
)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXTERNAL = ("http://", "https://", "mailto:", "data:")


def _targets(page: Path) -> list[str]:
    text = page.read_text(encoding="utf-8")
    found: list[str] = []
    for raw in LINK_RE.findall(text):
        href = raw.strip()
        if href.startswith(EXTERNAL) and os.environ.get("LODESTONE_CHECK_EXTERNAL") != "1":
            continue
        found.append(href)
    return found


def _resolve(page: Path, href: str) -> Path | None:
    if href.startswith(EXTERNAL):
        return None
    path_part = href.split("#", 1)[0]
    if not path_part or path_part.startswith("#"):
        return None
    if path_part.startswith("/"):
        return ROOT / path_part.lstrip("/")
    return (page.parent / path_part).resolve()


def main() -> None:
    missing_pages = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    failures: list[str] = []
    if missing_pages:
        failures.extend(f"missing required page: {name}" for name in missing_pages)
    for page in REQUIRED:
        if not page.is_file():
            continue
        for href in _targets(page):
            target = _resolve(page, href)
            if target is None:
                continue
            try:
                target.relative_to(ROOT)
            except ValueError:
                failures.append(f"{page.relative_to(ROOT)}: {href} escapes the repository")
                continue
            if not target.exists():
                failures.append(f"{page.relative_to(ROOT)}: broken link {href}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Link check: {len(REQUIRED)} pages, internal targets exist")


if __name__ == "__main__":
    main()
