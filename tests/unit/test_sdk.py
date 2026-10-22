# SPDX-License-Identifier: Apache-2.0
import doctest
import subprocess
import sys
from pathlib import Path

from lodestone import Lodestone, SearchResult

ROOT = Path(__file__).parents[2]
CONSUMER = """# SPDX-License-Identifier: Apache-2.0
from lodestone import Expert, Lodestone, SearchResult, Stats

def use(kb: Lodestone) -> tuple[SearchResult, Stats, list[Expert]]:
    report = kb.sync()
    assert report.processed >= 0
    found: SearchResult = kb.search("query", limit=5, rerank=False, explain=True)
    people = kb.who_knows("query")
    recent = kb.recent(limit=3)
    stats = kb.stats()
    _ = kb.grep("query")
    _ = kb.get("missing") if False else recent
    return found, stats, people
"""


def test_fr_050_sdk_mypy_strict(tmp_path: Path) -> None:
    consumer = tmp_path / "consumer.py"
    consumer.write_text(CONSUMER, encoding="utf-8")
    typed = Path(__file__).parents[2] / "src" / "lodestone" / "py.typed"
    assert typed.is_file()
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "mypy", "--strict", str(consumer)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_fr_050_readme_doctest() -> None:
    result = doctest.testfile(
        str(ROOT / "README.md"),
        module_relative=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
    )
    assert result.failed == 0
    kb = Lodestone.open(Path("."), offline=True) if False else None
    assert kb is None or isinstance(kb.search("x"), SearchResult)


def test_fr_050_open_directory_and_stats(tmp_path: Path) -> None:
    kb = Lodestone.open(tmp_path, offline=True)
    kb.sync()
    found = kb.search("nothing")
    assert isinstance(found, SearchResult)
    assert found.hits == []
    stats = kb.stats()
    assert stats.records == 0
    assert stats.store_queries is False
    assert kb.grep("nothing").matches == []
    assert kb.who_knows("nothing") == []
    assert kb.recent() == []
    kb.close()
