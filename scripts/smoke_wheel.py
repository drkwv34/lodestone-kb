# SPDX-License-Identifier: Apache-2.0
"""Exercise installed CLI and SQL package data outside the checkout."""

import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        for args in (["init"], ["doctor"], ["config", "show"]):
            subprocess.run(["lodestone", *args], cwd=Path(directory), check=True)  # noqa: S603,S607


if __name__ == "__main__":
    main()
