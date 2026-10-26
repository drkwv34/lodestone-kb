# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from lodestone.storage.consistency import deep_errors
from lodestone.storage.db import open_database

CHILD = Path(__file__).with_name("crash_child.py")


def _workspace(tmp_path: Path, n_files: int) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    for index in range(n_files):
        (docs / f"n{index}.md").write_text(f"# N{index}\ncrash token {index}\n", encoding="utf-8")
    return tmp_path


def _run_killed(workspace: Path, crash_after: int) -> None:
    env = os.environ.copy()
    env["LODESTONE_CRASH_AFTER"] = str(crash_after)
    subprocess.run(  # noqa: S603
        [sys.executable, str(CHILD), str(workspace)],
        check=False,
        env=env,
        cwd=str(workspace),
        timeout=60,
    )


def _assert_consistent(workspace: Path) -> None:
    db = workspace / ".lodestone/index.db"
    if not db.exists():
        return
    connection = open_database(db)
    try:
        assert deep_errors(connection) == []
    finally:
        connection.close()


def test_nfr_006_crash_injection_sigkill(tmp_path: Path) -> None:
    for index in range(3):
        workspace = _workspace(tmp_path / f"w{index}", n_files=8)
        _run_killed(workspace, crash_after=index)
        _assert_consistent(workspace)


@pytest.mark.slow
def test_nfr_006_crash_injection_50_iterations(tmp_path: Path) -> None:
    outcomes = {"consistent": 0}
    for index in range(50):
        workspace = _workspace(tmp_path / f"iter{index}", n_files=12)
        _run_killed(workspace, crash_after=index % 6)
        _assert_consistent(workspace)
        outcomes["consistent"] += 1
    assert outcomes["consistent"] == 50
