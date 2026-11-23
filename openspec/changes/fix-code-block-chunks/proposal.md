# Proposal

## Why

The code chunker detects `if`/`for` (and similar) blocks at symbol level 2, but
chunk cuts only keep those blocks when the enclosing method exceeds
`target_tokens`. Default limits leave the Cerebras figure (`processor.py`) as
three method-level chunks instead of the class → method → `if`/`for` children
required by FR-016.

## What Changes

- Emit block children under their method when the method exceeds
  `target_tokens` **or** when the coarse-to-fine rule applies (class/struct →
  function/method → block). Titles look like `processor > Processor > run > if`.
- Keep `tests/fixtures/chunking/figure.json` as the source of truth. Default
  chunk settings must reproduce those five chunks for `figure.code`.
- Bump `code.VERSION` so `content_hash` (FR-014) treats existing code files as
  changed. The next `sync` rewrites children, sets `derived_state` pending, and
  replaces old `ext_id` sequences. **BREAKING** for stored `code` child ids on
  files that contain blocks.
- Document the version bump in `docs/decisions/0010-code-block-children.md`.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `chunkers-sources`: FR-016 coarse-to-fine code chunks must emit block
  children under methods for the figure fixture under default (and tight)
  token targets, not only when the method is oversized.

## Impact

- `src/lodestone/chunking/code.py` cut selection and `VERSION`
- Ingest `content_hash` / `derived_state` rewrite path (no schema migration)
- Unit test `tests/unit/test_code_chunker.py::test_figure_fixture_matches`
- CLI `get processor.py --json` after syncing the figure as `processor.py`
- ADR 0010, CHANGELOG, evidence, PROGRESS
