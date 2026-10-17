# SPDX-License-Identifier: Apache-2.0
import logging
import shutil
from pathlib import Path

import pytest

from lodestone.config import Source
from lodestone.connectors.files import FilesConnector, jailed_path

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"


def test_fr_010_fixture_globs_gitignore_binary_oversize(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "corpus"
    shutil.copytree(CORPUS, root)
    (root / "huge.txt").write_bytes(b"x" * 301)
    (root / "invalid.txt").write_bytes(b"\xff\xfe")
    connector = FilesConnector()
    with caplog.at_level(logging.WARNING):
        items = list(
            connector.discover(
                Source(
                    name="wiki",
                    kind="files",
                    path=root,
                    include=["**/*.md", "**/*.txt", "**/*.rst"],
                    exclude=["drafts/**"],
                    max_file_bytes=300,
                )
            )
        )
    assert {item.ext_id for item in items} == {
        "manifest.md",
        "chatter.txt",
        "guide.rst",
        "nested/keep.txt",
    }
    skipped = {item.path: item.reason for item in connector.skipped}
    assert skipped["binary.txt"] == "binary"
    assert skipped["invalid.txt"] == "binary or invalid UTF-8"
    assert skipped["huge.txt"] == "oversize"
    assert skipped["ignored.txt"] == "ignored"
    assert skipped["nested/hidden.txt"] == "ignored"
    assert skipped["drafts/draft.md"] == "ignored"
    assert all(reason in caplog.text for reason in skipped.values())
    assert all(item.metadata["uri"].startswith("file:") for item in items)


@pytest.mark.parametrize(
    "path", ["../secret.txt", "/etc/passwd", r"..\secret.txt", r"C:\secret.txt"]
)
def test_fr_010_path_traversal(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match=r"traversal|absolute"):
        jailed_path(tmp_path, path)
    with pytest.raises(ValueError, match="patterns"):
        list(
            FilesConnector().discover(Source(name="x", kind="files", path=tmp_path, include=[path]))
        )


def test_fr_010_symlink_jail_and_cycles(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("outside secret")
    (root / "safe.txt").write_text("safe")
    try:
        (root / "escape.txt").symlink_to(outside)
        (root / "internal.txt").symlink_to(root / "safe.txt")
        (root / "loop").symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable on this platform")
    with pytest.raises(ValueError, match="escapes"):
        jailed_path(root, "escape.txt")
    connector = FilesConnector()
    items = list(connector.discover(Source(name="x", kind="files", path=root)))
    assert {item.ext_id for item in items} == {"safe.txt", "internal.txt"}
    assert all("outside secret" not in item.text for item in items)
    assert {skip.path for skip in connector.skipped} == {"escape.txt", "loop"}


def test_fr_010_gitignore_parent_and_nested_negation(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.txt\nblocked/\n")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".gitignore").write_text("!keep.txt\n")
    (nested / "keep.txt").write_text("keep")
    (nested / "hide.txt").write_text("hide")
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / ".gitignore").write_text("!hidden.txt")
    (blocked / "hidden.txt").write_text("hide")
    connector = FilesConnector()
    items = list(connector.discover(Source(name="x", kind="files", path=tmp_path)))
    assert [item.ext_id for item in items] == ["nested/keep.txt"]


def test_fr_010_defaults_and_unsupported(tmp_path: Path) -> None:
    (tmp_path / "ignored.csv").write_text("pass")
    (tmp_path / "big.txt").write_bytes(b"x" * (1024 * 1024 + 1))
    connector = FilesConnector()
    assert list(connector.discover(Source(name="x", kind="files", path=tmp_path))) == []
    assert {skip.reason for skip in connector.skipped} == {
        "oversize",
        "unsupported extension",
    }


def test_fr_010_gitignore_limit_independent_and_fail_closed(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("# longer than the document limit\nhidden.txt\n")
    (tmp_path / "hidden.txt").write_text("hide")
    connector = FilesConnector()
    source = Source(name="x", kind="files", path=tmp_path, max_file_bytes=4)
    assert list(connector.discover(source)) == []
    assert connector.skipped[0].reason == "ignored"
    (tmp_path / ".gitignore").write_bytes(b"\xff")
    assert list(connector.discover(source)) == []
    assert connector.skipped[0].path == ".gitignore"


def test_fr_010_code_kinds_keep_file_safety_rules(tmp_path: Path) -> None:
    from lodestone.connectors.files import CODE_KINDS

    for language in CODE_KINDS:
        (tmp_path / f"valid.{language}").write_text("source text", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "ignored.py").write_text("pass")
    (tmp_path / "binary.js").write_bytes(b"\x00\x01")
    (tmp_path / "large.rs").write_text("x" * 101)
    connector = FilesConnector()
    found = list(
        connector.discover(Source(name="code", kind="files", path=tmp_path, max_file_bytes=100))
    )
    assert {item.ext_id for item in found} == {f"valid.{language}" for language in CODE_KINDS}
    assert {skip.reason for skip in connector.skipped} == {"ignored", "binary", "oversize"}
