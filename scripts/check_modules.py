# SPDX-License-Identifier: Apache-2.0
"""Blocking module size and SPDX gate, shared by CI and pre-commit."""

from pathlib import Path


def main() -> None:
    failures: list[str] = []
    paths = sorted(
        path for root in ("src", "tests", "scripts") for path in Path(root).rglob("*.py")
    )
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 500:
            failures.append(f"{path}: {len(lines)} lines exceeds 500")
        if not lines or lines[0] != "# SPDX-License-Identifier: Apache-2.0":
            failures.append(f"{path}: missing SPDX header")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Module gate: {len(paths)} Python files <= 500 lines, all SPDX headers present")


if __name__ == "__main__":
    main()
