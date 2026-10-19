# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from lodestone.cli import app
from lodestone.config import load_config
from lodestone.workspace import search_workspace

ROOT = Path(__file__).parents[2]
EXPORT = ROOT / "tests/fixtures/slack_export"
SCRIPT = ROOT / "examples/slack_export_to_jsonl.py"
runner = CliRunner()


def load_example():
    spec = importlib.util.spec_from_file_location("slack_export_to_jsonl", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fr_011_slack_export_example_converts_fixture(tmp_path: Path) -> None:
    out = tmp_path / "threads.jsonl"
    module = load_example()
    threads = module.convert(EXPORT)
    assert len(threads) == 1
    assert threads[0]["thread_id"] == "1719830040.000100"
    assert [message["author"] for message in threads[0]["messages"]] == ["maya", "owen"]
    assert threads[0]["messages"][1]["reactions"] == 2
    assert threads[0]["messages"][0]["ts"].endswith("Z")
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), str(EXPORT), "--out", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert lines == threads


def test_fr_011_fr_012_threads_sync_search_smoke(tmp_path: Path) -> None:
    exported = tmp_path / "support.jsonl"
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), str(EXPORT), "--out", str(exported)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    workspace = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(workspace)]).exit_code == 0
    config = workspace / "lodestone.toml"
    args = ["--config", str(config)]
    added = runner.invoke(
        app,
        ["source", "add", "support", "--kind", "threads", "--path", str(exported), *args],
    )
    assert added.exit_code == 0, added.output
    first = runner.invoke(app, ["sync", "--provider", "fake", *args])
    assert first.exit_code == 0, first.output
    payload = json.loads(first.stdout)
    assert payload["processed"] == 1
    cfg = load_config(config)
    hits = search_workspace(cfg, "CKPT_PREFETCH", kinds=["thread", "burst"])
    assert hits
    second = runner.invoke(app, ["sync", "--provider", "fake", *args])
    assert json.loads(second.stdout)["processed"] == 0
    raw = json.loads(exported.read_text().splitlines()[0])
    raw["messages"].append(
        {
            "id": "m3",
            "author": "maya",
            "ts": "2026-07-01T12:00:00Z",
            "text": "APPENDED_THREAD_TOKEN confirming the replace.",
        }
    )
    exported.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    third = runner.invoke(app, ["sync", "--provider", "fake", *args])
    assert json.loads(third.stdout)["processed"] == 1
    later = search_workspace(cfg, "APPENDED_THREAD_TOKEN", kinds=["thread"])
    assert later and later[0].ext_id == "1719830040.000100"


def test_fr_011_example_script_rejects_missing_directory(tmp_path: Path) -> None:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), str(tmp_path / "missing")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "directory" in completed.stderr.lower()
