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

## PR head CI

- PR: https://github.com/drkwv34/lodestone-kb/pull/19
- Head SHA: `709c95f7cc1a7ade454a59a5809823f84116768d`
- Run: https://github.com/drkwv34/lodestone-kb/actions/runs/45094685851
- Conclusion: success (10/10 jobs)

## Merge

```text
$ git merge --no-ff fix/code-block-chunks -m "Merge pull request #19 from drkwv34/fix/code-block-chunks"
Merge made by the 'ort' strategy.
```

Merge commit: `73a21d8e969bca5b899591622003a694c966b38e`
Author and committer: Christian Agila `<87576768+drkwv34@users.noreply.github.com>`
Message is exactly one line: `Merge pull request #19 from drkwv34/fix/code-block-chunks`

## Archive (on main)

```text
$ openspec archive fix-code-block-chunks --yes --skip-specs
Task status: ✓ Complete
Skipping spec updates (--skip-specs flag provided).
Change 'fix-code-block-chunks' archived as '2026-11-23-fix-code-block-chunks'.

$ openspec validate --all --strict
✓ spec/beir-adapter
✓ spec/bench-agentic-advise
✓ spec/bench-formats-synth
✓ spec/chunkers-sources
✓ spec/docs-packaging
✓ spec/fusion-search
✓ spec/hardening
✓ spec/lexical-search
✓ spec/mcp-ask
✓ spec/mcp-container
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 16 passed, 0 failed (16 items)
```

Main specs were synced from the change delta before `--skip-specs` (FR-016).
`ruff format .` left 333 files unchanged.
