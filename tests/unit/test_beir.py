# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from lodestone.bench.beir import BeirError, import_beir, md5_digest
from lodestone.bench.evalset import load_evalset
from lodestone.config import Source
from lodestone.connectors.files import FilesConnector

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/beir/scifact"


def test_fr_079_offline_fixture_imports_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(url: str) -> bytes:  # pragma: no cover - must not run
        raise AssertionError(f"unexpected download {url}")

    monkeypatch.setattr("lodestone.bench.beir.http_get", blocked)
    result = import_beir("beir:scifact", tmp_path / "out", source=FIXTURE, fetch=blocked)
    assert result.documents == 2
    assert result.questions == 2
    rows = load_evalset(result.evalset)
    by_qid = {row.qid: row for row in rows}
    assert by_qid["q1"].gold_ids == ["docs/d1.md"]
    assert by_qid["q1"].category == "paraphrase"
    assert by_qid["q2"].gold_ids == []
    assert by_qid["q2"].category == "unanswerable"
    items = list(
        FilesConnector().discover(
            Source(name="docs", kind="files", path=result.directory, include=["docs/**"])
        )
    )
    ext_ids = {item.ext_id for item in items}
    assert "docs/d1.md" in ext_ids
    assert "ERR_MANIFEST_TIMEOUT" in (result.directory / "docs/d1.md").read_text(encoding="utf-8")


def test_fr_079_checksum_mismatch_rejects(tmp_path: Path) -> None:
    def fake(_url: str) -> bytes:
        return b"not-the-scifact-zip"

    with pytest.raises(BeirError, match="checksum mismatch"):
        import_beir("beir:scifact", tmp_path / "out", fetch=fake)
    assert not (tmp_path / "out" / "evalset.jsonl").exists()


def test_fr_079_local_zip_and_unknown_dataset(tmp_path: Path) -> None:
    archive = tmp_path / "tiny.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for path in FIXTURE.rglob("*"):
            if path.is_file():
                handle.write(path, path.relative_to(FIXTURE.parent).as_posix())
    result = import_beir("beir:scifact", tmp_path / "from-zip", source=archive)
    assert result.questions == 2
    with pytest.raises(BeirError, match="unsupported"):
        import_beir("beir:msmarco", tmp_path / "bad", source=FIXTURE)


def test_fr_079_download_with_matching_checksum(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "tiny.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for path in FIXTURE.rglob("*"):
            if path.is_file():
                handle.write(path, path.relative_to(FIXTURE.parent).as_posix())
    payload = archive.read_bytes()
    monkeypatch.setattr("lodestone.bench.beir.SCIFACT_MD5", md5_digest(payload))
    result = import_beir("beir:scifact", tmp_path / "downloaded", fetch=lambda _url: payload)
    assert result.documents == 2
    assert load_evalset(result.evalset)


@pytest.mark.network
def test_fr_079_network_download_is_opt_in(tmp_path: Path) -> None:
    if os.environ.get("LODESTONE_NETWORK_TESTS") != "1":
        pytest.skip("set LODESTONE_NETWORK_TESTS=1 to hit the public SciFact zip")
    result = import_beir("beir:scifact", tmp_path / "scifact")
    assert result.questions > 0
    load_evalset(result.evalset)
