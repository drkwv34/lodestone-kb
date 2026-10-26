# SPDX-License-Identifier: Apache-2.0
"""Child process for SIGKILL crash injection."""

from __future__ import annotations

import sys
from pathlib import Path

from lodestone.config import load_config
from lodestone.workspace import initialise, sync_workspace


def main() -> None:
    workspace = Path(sys.argv[1])
    initialise(workspace)
    config_path = workspace / "lodestone.toml"
    if "wiki" not in config_path.read_text(encoding="utf-8"):
        text = config_path.read_text(encoding="utf-8").replace("sources = []", 'sources = ["wiki"]')
        config_path.write_text(
            text + '\n[[sources]]\nname="wiki"\nkind="files"\npath="docs"\n',
            encoding="utf-8",
        )
    sync_workspace(load_config(config_path), offline=True)


if __name__ == "__main__":
    main()
