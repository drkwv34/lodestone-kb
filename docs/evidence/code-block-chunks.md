# Code block children under methods

Branch: `fix/code-block-chunks`.
OpenSpec change: `fix-code-block-chunks`.

Implements FR-016 coarse-to-fine cuts so `if`/`for` blocks become children of
their method under default token limits, with `code.VERSION` bumped to
`code-v2` so FR-014 rewrites stored children on the next sync.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
2.1.1

$ openspec validate fix-code-block-chunks --strict
Change 'fix-code-block-chunks' is valid
```

## Tests on base (must fail)

Default `Chunks()` emits three method-level chunks; figure.json expects five.

```text
FAILED tests/unit/test_code_chunker.py::test_figure_fixture_matches
```

## Tests after the fix

```text
$ python3 -m pytest -q \
    tests/unit/test_code_chunker.py::test_figure_fixture_matches \
    tests/e2e/test_code_cli.py::test_fr_016_get_processor_json_matches_figure \
    tests/integration/test_ingest.py::test_fr_014_fr_016_chunker_version_rewrites_code_children \
    --no-cov
............                                                             [100%]
12 passed in 1.24s
```

Full default pytest: 242 passed, coverage 91.86% (>= 85%).
`openspec validate fix-code-block-chunks --strict`: Change is valid.
