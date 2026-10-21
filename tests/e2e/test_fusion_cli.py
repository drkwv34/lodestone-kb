# SPDX-License-Identifier: Apache-2.0
import json
import shutil
from pathlib import Path

from tests.e2e.test_lexical_cli import command

CORPUS = Path(__file__).parents[1] / "fixtures/corpus"


def test_fr_040_fr_034_fused_explain_and_grep_cli(tmp_path: Path) -> None:
    shutil.copytree(CORPUS, tmp_path / "corpus")
    assert command(tmp_path, "init").returncode == 0
    config_path = tmp_path / "lodestone.toml"
    config_path.write_text(config_path.read_text().replace("sources = []", 'sources = ["wiki"]'))
    with config_path.open("a") as stream:
        stream.write(
            '\n[[sources]]\nname="wiki"\nkind="files"\npath="corpus"\nexclude=["drafts/**"]\n'
        )
    synced = command(tmp_path, "sync", "--offline")
    assert synced.returncode == 0, synced.stderr
    explained = command(
        tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--explain", "--json", "--offline"
    )
    assert explained.returncode == 0, explained.stderr
    payload = json.loads(explained.stdout)
    assert payload["lane"] == "fused"
    assert payload["hits"]
    explain = payload["hits"][0]["explain"]
    contributions = [info["contribution"] for info in explain.values() if isinstance(info, dict)]
    assert contributions
    assert abs(sum(contributions) * explain["decay_factor"] - explain["final"]) < 1e-9
    human = command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--explain", "--offline")
    assert human.returncode == 0, human.stderr
    assert "explain:" in human.stdout
    grep = command(tmp_path, "search", "ERR_MANIFEST_TIMEOUT", "--lane", "grep", "--json")
    assert grep.returncode == 0, grep.stderr
    grep_payload = json.loads(grep.stdout)
    assert grep_payload["lane"] == "grep"
    assert grep_payload["hits"]
    rejected = command(tmp_path, "search", "(a+)+", "--lane", "grep", "--regex")
    assert rejected.returncode == 2
    assert "pathological" in rejected.stderr
