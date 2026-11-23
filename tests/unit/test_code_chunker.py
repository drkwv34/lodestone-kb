# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from lodestone.chunking import code
from lodestone.config import Chunks

FIXTURES = Path(__file__).parents[1] / "fixtures/chunking"


def test_figure_fixture_matches() -> None:
    text = (FIXTURES / "figure.code").read_text()
    expected = json.loads((FIXTURES / "figure.json").read_text())
    chunks = code.chunk(text, "py", "processor")
    assert [{"title": item.title, "text": item.text} for item in chunks] == expected
    assert [item.title for item in chunks] == [
        "processor > Processor",
        "processor > Processor > run",
        "processor > Processor > run > if",
        "processor > Processor > run > for",
        "processor > Processor > stop",
    ]
    assert code.outline(text, "py") == ("class Processor:\ndef run(self, items):\ndef stop(self):")
    assert "".join(item.text for item in chunks) == text
    tight = code.chunk(text, "py", "processor", Chunks(target_tokens=40, max_tokens=80))
    assert [{"title": item.title, "text": item.text} for item in tight] == expected
