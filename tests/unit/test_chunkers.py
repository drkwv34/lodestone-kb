# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from lodestone.chunking import code, markdown
from lodestone.config import Chunks

FIXTURES = Path(__file__).parents[1] / "fixtures/chunking"


def test_fr_015_heading_path_golden() -> None:
    text = (FIXTURES / "headings.md").read_text()
    chunks = markdown.chunk(text, "Manual")
    assert [{"title": item.title, "text": item.text} for item in chunks] == json.loads(
        (FIXTURES / "headings.json").read_text()
    )
    assert "".join(item.text for item in chunks) == text
    assert all(text[item.start : item.end] == item.text for item in chunks)


def test_fr_015_fence_atomicity_limits_and_paragraph_target() -> None:
    fence = "```python\n# not a heading\nprint('hello')\n```\n"
    text = "# Guide\n\n" + "words " * 8 + "\n\n" + fence + "\n" + "last " * 8
    cfg = Chunks(target_tokens=10, max_tokens=30)
    chunks = markdown.chunk(text, config=cfg)
    assert len(chunks) > 1
    assert all(item.title == "Guide" for item in chunks)
    assert sum(fence in item.text for item in chunks) == 1
    assert all(len(item.text) <= 120 for item in chunks)
    assert "".join(item.text for item in chunks) == text
    oversized = "~~~\n" + "x" * 500 + "\n~~~\n"
    parts = markdown.chunk(oversized, config=cfg)
    assert len(parts) > 1
    assert max(len(item.text) for item in parts) <= 120
    assert "".join(item.text for item in parts) == oversized
    assert markdown.chunk("") == []
    assert [item.title for item in markdown.chunk("# A\n### B\n## C\n# D\n")] == [
        "A",
        "A > B",
        "A > C",
        "D",
    ]
    assert len(markdown.chunk("````\n# literal\n```\n# still literal\n````\n")) == 1


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=800))
def test_fr_015_lossless_bounded_text_property(text: str) -> None:
    config = Chunks(target_tokens=8, max_tokens=16, chars_per_token=2)
    chunks = markdown.chunk(text, config=config)
    assert "".join(item.text for item in chunks) == text
    assert all(len(item.text) <= 32 for item in chunks)
    with pytest.raises(ValidationError):
        Chunks(target_tokens=17, max_tokens=16)


def test_fr_016_class_method_if_for_golden() -> None:
    text = (FIXTURES / "figure.code").read_text()
    chunks = code.chunk(text, "py", "processor", Chunks(target_tokens=40, max_tokens=80))
    assert [{"title": item.title, "text": item.text} for item in chunks] == json.loads(
        (FIXTURES / "figure.json").read_text()
    )
    assert code.outline(text, "py") == ("class Processor:\ndef run(self, items):\ndef stop(self):")
    assert "".join(item.text for item in chunks) == text
    assert all(text[item.start : item.end] == item.text for item in chunks)


@pytest.mark.parametrize(
    ("language", "text", "signatures", "titles"),
    [
        (
            "py",
            "class A:\n    def f(self):\n        return 1\n",
            "class A:\ndef f(self):",
            ["unit > A", "unit > A > f"],
        ),
        (
            "js",
            "class A {\n  f(x) { return x; }\n}\n",
            "class A {\nf(x) { return x; }",
            ["unit > A", "unit > A > f"],
        ),
        (
            "ts",
            "class A {\n  public f(x: number): number { return x; }\n}\n",
            "class A {\npublic f(x: number): number { return x; }",
            ["unit > A", "unit > A > f"],
        ),
        (
            "go",
            "type A struct { value int }\nfunc (a A) f() int { return a.value }\n",
            "type A struct { value int }\nfunc (a A) f() int { return a.value }",
            ["unit > A", "unit > f"],
        ),
        (
            "java",
            "class A {\n public int f() { return 1; }\n}\n",
            "class A {\npublic int f() { return 1; }",
            ["unit > A", "unit > A > f"],
        ),
        (
            "c",
            "struct A { int x; };\nint f(void) { return 1; }\n",
            "struct A { int x; };\nint f(void) { return 1; }",
            ["unit > A", "unit > f"],
        ),
        (
            "cpp",
            "class A {\n int f() { return 1; }\n};\n",
            "class A {\nint f() { return 1; }",
            ["unit > A", "unit > A > f"],
        ),
        (
            "rs",
            "impl A {\n pub fn f(&self) -> i32 { 1 }\n}\n",
            "impl A {\npub fn f(&self) -> i32 { 1 }",
            ["unit > A", "unit > A > f"],
        ),
    ],
)
def test_fr_016_fr_010_language_goldens(language, text, signatures, titles) -> None:
    assert code.outline(text, language) == signatures
    chunks = code.chunk(text, language, "unit")
    assert [item.title for item in chunks] == titles
    assert "".join(item.text for item in chunks) == text


def test_fr_016_comments_strings_and_fallback() -> None:
    text = '// class Fake {}\nconst s = "class Fake { }";\nfunction real() {\n return "}";\n}\n'
    assert code.outline(text, "js") == "function real() {"
    assert [item.title for item in code.chunk(text, "js", "file")] == ["file", "file > real"]
    for language in [*code.LANGUAGES, "unknown"]:
        raw = "x" * 500 + "\n\n" + "value " * 80
        chunks = code.chunk(raw, language, config=Chunks(target_tokens=10, max_tokens=20))
        assert "".join(item.text for item in chunks) == raw
        assert all(len(item.text) <= 80 for item in chunks)
    assert code.chunk("", "py") == []
