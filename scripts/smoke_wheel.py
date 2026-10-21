# SPDX-License-Identifier: Apache-2.0
"""Exercise installed CLI and SQL package data outside the checkout."""

import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for args in (["init"], ["doctor"], ["config", "show"]):
            subprocess.run(["lodestone", *args], cwd=root, check=True)  # noqa: S603,S607
        (root / "docs").mkdir()
        (root / "docs/manifest.md").write_text("ERR_MANIFEST_TIMEOUT", encoding="utf-8")
        subprocess.run(
            ["lodestone", "source", "add", "wiki", "--path", "docs"],  # noqa: S607
            cwd=root,
            check=True,
        )
        subprocess.run(["lodestone", "sync"], cwd=root, check=True)  # noqa: S607
        result = subprocess.run(
            ["lodestone", "search", "ERR_MANIFEST_TIMEOUT", "--json"],  # noqa: S607
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
        fused = '"schema": "evidence.v1"' in result.stdout
        if not fused or "ERR_MANIFEST_TIMEOUT" not in result.stdout:
            raise RuntimeError(f"Installed wheel fused search failed: {result.stdout}")
        print("Wheel smoke: init, doctor, config, sync, fused search passed")


if __name__ == "__main__":
    main()
