# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from tests.e2e.test_lexical_cli import command

FIGURE = Path(__file__).parents[1] / "fixtures/chunking"


def test_fr_016_get_processor_json_matches_figure(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "processor.py").write_text((FIGURE / "figure.code").read_text(), encoding="utf-8")
    expected = json.loads((FIGURE / "figure.json").read_text())
    assert command(tmp_path, "init").returncode == 0
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(config_path.read_text().replace("sources = []", 'sources = ["code"]'))
    with config_path.open("a") as stream:
        stream.write('\n[[sources]]\nname="code"\nkind="files"\npath="corpus"\n')
    synced = command(tmp_path, "sync", "--offline")
    assert synced.returncode == 0, synced.stderr
    got = command(tmp_path, "get", "processor.py", "--json")
    assert got.returncode == 0, got.stderr
    view = json.loads(got.stdout)
    assert view["kind"] == "code_file"
    assert view["ext_id"] == "processor.py"
    titles = [child["title"] for child in view["children"]]
    assert titles == [item["title"] for item in expected]
    snippets = [child["snippet"] for child in view["children"]]
    for item, snippet in zip(expected, snippets, strict=True):
        assert snippet == item["text"].replace("\n", " ")[:240]
