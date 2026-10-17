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
        with (root / "lodestone.toml").open("a", encoding="utf-8") as stream:
            stream.write('\n[[sources]]\nname="wiki"\nkind="files"\npath="docs"\n')
        subprocess.run(["lodestone", "sync"], cwd=root, check=True)  # noqa: S607
        result = subprocess.run(
            ["lodestone", "search", "ERR_MANIFEST_TIMEOUT", "--json"],  # noqa: S607
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
        if '"ext_id": "manifest.md"' not in result.stdout:
            raise RuntimeError("Installed wheel lexical search failed")
        print("Wheel smoke: init, doctor, config, sync, search passed")


if __name__ == "__main__":
    main()
