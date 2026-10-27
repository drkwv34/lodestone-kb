# SPDX-License-Identifier: Apache-2.0
"""Exercise installed CLI and SQL package data outside the checkout."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def lodestone_cmd() -> str:
    bindir = Path(sys.executable).resolve().parent
    candidate = bindir / ("lodestone.exe" if os.name == "nt" else "lodestone")
    if candidate.is_file():
        return str(candidate)
    return "lodestone"


def main() -> None:
    cli = lodestone_cmd()
    env = os.environ.copy()
    bindir = str(Path(sys.executable).resolve().parent)
    env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for args in (["init"], ["doctor"], ["config", "show"]):
            subprocess.run([cli, *args], cwd=root, check=True, env=env)  # noqa: S603
        (root / "docs").mkdir()
        (root / "docs/manifest.md").write_text("ERR_MANIFEST_TIMEOUT", encoding="utf-8")
        subprocess.run(  # noqa: S603
            [cli, "source", "add", "wiki", "--path", "docs"],
            cwd=root,
            check=True,
            env=env,
        )
        subprocess.run([cli, "sync"], cwd=root, check=True, env=env)  # noqa: S603
        result = subprocess.run(  # noqa: S603
            [cli, "search", "ERR_MANIFEST_TIMEOUT", "--json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        fused = '"schema": "evidence.v1"' in result.stdout
        if not fused or "ERR_MANIFEST_TIMEOUT" not in result.stdout:
            raise RuntimeError(f"Installed wheel fused search failed: {result.stdout}")
        print("Wheel smoke: init, doctor, config, sync, fused search passed")


if __name__ == "__main__":
    main()
