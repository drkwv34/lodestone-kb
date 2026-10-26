# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

from lodestone.config import Config, Source
from lodestone.connectors.files import jailed_path
from lodestone.ingest.pipeline import sync
from lodestone.lanes.grep import rg_argv, run_rg
from lodestone.observe import scrub

ROOT = Path(__file__).resolve().parents[2] / "src/lodestone"


def test_nfr_008_path_jail_and_log_scrub(
    database, tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CEREBRAS_API_KEY", "super-secret-api-key-value")
    root = tmp_path / "root"
    root.mkdir()
    (root / "ok.txt").write_text("safe token", encoding="utf-8")
    with pytest.raises(ValueError, match=r"traversal|absolute"):
        jailed_path(root, "../secret.txt")
    with caplog.at_level(logging.INFO):
        report = sync(database, Config(sources=[Source(name="docs", kind="files", path=root)]))
    assert report.processed >= 1
    assert "super-secret-api-key-value" not in caplog.text
    assert "super-secret-api-key-value" not in str(scrub("token=super-secret-api-key-value"))


def test_nfr_009_no_shell_rg_argument_arrays(monkeypatch: pytest.MonkeyPatch) -> None:
    argv = rg_argv("ERR_MANIFEST_TIMEOUT", ["corpus"], regex=False)
    assert argv[0] == "rg"
    assert "-e" in argv
    assert "ERR_MANIFEST_TIMEOUT" in argv
    assert all(isinstance(part, str) for part in argv)

    monkeypatch.setattr("lodestone.lanes.grep.shutil.which", lambda name: "/usr/bin/rg")
    recorded: list[tuple[object, dict[str, object]]] = []

    def fake_run(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")  # type: ignore[arg-type]

    monkeypatch.setattr("lodestone.lanes.grep.subprocess.run", fake_run)
    run_rg("token", ["corpus"], regex=False)
    command, kwargs = recorded[0]
    assert isinstance(command, list)
    assert kwargs.get("shell") is False
    banned = ("shell=True", "os.system(", "os.popen(")
    for path in ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path} contains {token}"
