# SPDX-License-Identifier: Apache-2.0
"""Workspace setup and the Day 1 local runtime diagnostic."""

from pathlib import Path

from lodestone.config import DEFAULT_TOML, load_config
from lodestone.storage.db import open_database


def initialise(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "lodestone.toml"
    existed = config_path.exists()
    if not existed:
        try:
            with config_path.open("x", encoding="utf-8") as stream:
                stream.write(DEFAULT_TOML)
        except FileExistsError:
            existed = True
    config = load_config(config_path)
    database_existed = config.workspace.db_path.exists()
    connection = open_database(config.workspace.db_path)
    connection.close()
    return existed and database_existed
