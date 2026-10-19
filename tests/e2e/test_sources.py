# SPDX-License-Identifier: Apache-2.0
import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lodestone.cli import app
from lodestone.config import load_config
from lodestone.config_io import replace_config
from lodestone.storage.db import open_database
from lodestone.workspace import search_workspace

runner = CliRunner()


def test_fr_004_fr_003_fr_005_source_lifecycle_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LODESTONE_LLM_API_KEY", "private-override")
    workspace = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(workspace)]).exit_code == 0
    config_path = workspace / "lodestone.toml"
    original = config_path.read_text()
    config_path.write_text(original + '\n[llm]\nmodel="local"\n')
    roots = [tmp_path / name for name in ("wiki", "code")]
    for name, root in zip(("wiki", "code"), roots, strict=True):
        root.mkdir()
        (root / "guide.md").write_text(f"# Guide\nshared {name}_unique\n")
    config_args = ["--config", str(config_path)]
    for name, root in zip(("wiki", "code"), roots, strict=True):
        result = runner.invoke(
            app,
            [
                "source",
                "add",
                name,
                "--kind",
                "files",
                "--path",
                str(root),
                "--include",
                "**/*.md",
                *config_args,
            ],
        )
        assert result.exit_code == 0, result.output
        assert f"Added source: {name}" in result.output
    listed = runner.invoke(app, ["source", "list", *config_args])
    assert listed.exit_code == 0
    assert [source["name"] for source in json.loads(listed.output)] == ["wiki", "code"]
    assert "private-override" not in listed.output + config_path.read_text()
    assert load_config(config_path).llm.model == "local"
    for name in ("wiki", "code"):
        result = runner.invoke(app, ["source", "sync", name, *config_args])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["processed"] == 1
    cfg = load_config(config_path)
    connection = open_database(cfg.workspace.db_path)
    try:
        ids = [
            row[0]
            for row in connection.execute(
                "SELECT r.id FROM records r JOIN sources s ON s.id=r.source_id WHERE s.name='wiki'"
            )
        ]
        with connection:
            for record_id in ids:
                connection.execute(
                    "INSERT INTO embeddings VALUES(?,'chunk','local',1,X'00000000')", (record_id,)
                )
        assert connection.execute("SELECT df FROM term_stats WHERE term='shared'").fetchone() == (
            4,
        )
        removed = runner.invoke(app, ["source", "remove", "wiki", *config_args])
        assert removed.exit_code == 0, removed.output
        cfg = load_config(config_path)
        assert [source.name for source in cfg.sources] == ["code"]
        assert cfg.projects[0].sources == ["code"]
        assert search_workspace(cfg, "wiki_unique") == []
        assert search_workspace(cfg, "code_unique")
        assert connection.execute("SELECT count(*) FROM embeddings").fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM records WHERE id IN (?,?)", ids
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM records_vocab WHERE term='wiki_unique'"
        ).fetchone() == (0,)
        assert connection.execute("SELECT df FROM term_stats WHERE term='shared'").fetchone() == (
            2,
        )
        assert (
            connection.execute("SELECT df FROM term_stats WHERE term='wiki_unique'").fetchone()
            is None
        )
        assert dict(connection.execute("SELECT term,df FROM term_stats")) == dict(
            connection.execute("SELECT term,count(*) FROM record_terms GROUP BY term")
        )
        assert connection.execute("SELECT count(*) FROM project_sources").fetchone() == (1,)
        assert connection.execute(
            "SELECT count(*) FROM record_terms WHERE record_id IN (?,?)", ids
        ).fetchone() == (0,)
        connection.execute("INSERT INTO records_fts(records_fts,rank) VALUES('integrity-check',1)")
    finally:
        connection.close()
    (roots[1] / "guide.md").unlink()
    pruned = runner.invoke(app, ["source", "sync", "code", "--prune", *config_args])
    assert pruned.exit_code == 0, pruned.output
    assert json.loads(pruned.output)["pruned"] == 1
    result = runner.invoke(app, ["source", "remove", "code", *config_args])
    assert result.exit_code == 0
    with sqlite3.connect(cfg.workspace.db_path) as connection:
        for table in (
            "sources",
            "records",
            "records_vocab",
            "term_stats",
            "record_terms",
            "project_sources",
        ):
            assert connection.execute("SELECT count(*) FROM " + table)  # noqa: S608 - fixed table names.fetchone() == (0,)


def test_fr_003_fr_004_cli_scope_and_errors(tmp_path: Path) -> None:
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    path = tmp_path / "lodestone.toml"
    path.write_text(path.read_text() + '\n[[projects]]\nname="private"\nsources=[]\n')
    root = tmp_path / "docs"
    root.mkdir()
    (root / "one.md").write_text("needle")
    cfg = ["--config", str(path)]
    add = ["source", "add", "notes", "--path", str(root)]
    assert runner.invoke(app, [*add, "--project", "private", *cfg]).exit_code == 0
    assert json.loads(runner.invoke(app, ["source", "list", *cfg]).output) == []
    assert json.loads(runner.invoke(app, ["sync", *cfg]).output)["processed"] == 0
    assert (
        json.loads(
            runner.invoke(app, ["source", "sync", "notes", "--project", "private", *cfg]).output
        )["processed"]
        == 1
    )
    result = runner.invoke(app, ["search", "needle", "--project", "private", "--json", *cfg])
    assert result.exit_code == 0, result.output
    assert {hit["source"] for hit in json.loads(result.output)["hits"]} == {"notes"}
    assert json.loads(runner.invoke(app, ["search", "needle", "--json", *cfg]).output)["hits"] == []
    for args in (
        [*add, "--project", "private"],
        [*add, "--kind", "threads"],
        ["source", "add", "other", "--path", str(root), "--include", "../*.md"],
        ["source", "add", "other", "--path", str(root / "missing")],
        ["source", "remove", "notes"],
        ["source", "list", "--project", "absent"],
        ["sync", "--project", "absent"],
        ["source", "sync", "absent"],
    ):
        result = runner.invoke(app, [*args, *cfg])
        assert result.exit_code == 2, result.output
    with sqlite3.connect(load_config(path).workspace.db_path) as connection:
        connection.execute("PRAGMA user_version=999")
    result = runner.invoke(app, ["source", "remove", "notes", "--project", "private", *cfg])
    assert result.exit_code == 1
    assert "newer" in result.output
    assert len(load_config(path).sources) == 1


def test_fr_004_atomic_config_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "lodestone.toml"
    path.write_text("schema_version=1\n")
    before = path.read_text()

    def fail(*args: object) -> None:
        raise OSError("injected rename failure")

    monkeypatch.setattr("lodestone.config_io.os.replace", fail)
    with pytest.raises(OSError, match="injected rename failure"):
        replace_config(path, "replacement")
    assert path.read_text() == before
    assert sorted(item.name for item in tmp_path.iterdir()) == ["lodestone.toml"]


def test_fr_004_failed_registry_update_preserves_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    path = tmp_path / "lodestone.toml"
    root = tmp_path / "docs"
    root.mkdir()
    (root / "file.md").write_text("# Guide\nretained_token\n")
    args = ["--config", str(path)]
    assert runner.invoke(app, ["source", "add", "wiki", "--path", str(root), *args]).exit_code == 0
    assert runner.invoke(app, ["sync", *args]).exit_code == 0
    raw = path.read_bytes()
    config = load_config(path)
    before = search_workspace(config, "retained_token")

    def fail(*args: object) -> None:
        raise OSError("injected rename failure")

    monkeypatch.setattr("lodestone.config_io.os.replace", fail)
    result = runner.invoke(app, ["source", "remove", "wiki", *args])
    assert result.exit_code == 1, result.output
    assert "injected rename failure" in result.output
    assert path.read_bytes() == raw
    assert search_workspace(config, "retained_token") == before
    with sqlite3.connect(config.workspace.db_path) as connection:
        assert connection.execute("SELECT count(*) FROM project_sources").fetchone() == (1,)
        assert connection.execute(
            "SELECT df FROM term_stats WHERE term='retained_token'"
        ).fetchone() == (2,)


def test_fr_004_register_thread_source_without_ingesting(tmp_path: Path) -> None:
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0
    path = tmp_path / "lodestone.toml"
    exported = tmp_path / "threads.jsonl"
    exported.write_text("")
    args = ["--config", str(path)]
    result = runner.invoke(
        app, ["source", "add", "support", "--kind", "threads", "--path", str(exported), *args]
    )
    assert result.exit_code == 0, result.output
    assert load_config(path).sources[0].kind == "threads"
    result = runner.invoke(app, ["source", "sync", "support", *args])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["processed"] == 0
    result = runner.invoke(app, ["source", "remove", "support", *args])
    assert result.exit_code == 0, result.output
