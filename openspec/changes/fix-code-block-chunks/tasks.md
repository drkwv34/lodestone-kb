# Tasks

## 1. Code chunker

- [x] 1.1 Cut method-enclosed block symbols even when the method is under `target_tokens`; keep class/method cuts and omit blocks from `outline()`. Verify `code.chunk(figure.code, "py", "processor")` with default `Chunks()` matches `figure.json`.
- [x] 1.2 Bump `code.VERSION` to `code-v2` so `CHUNKER_VERSION` changes parent hashes. Verify a second sync of an already-ingested `processor.py` rewrites children after the version bump (or an equivalent hash-miss upsert).

## 2. Tests and docs

- [x] 2.1 Add `tests/unit/test_code_chunker.py::test_figure_fixture_matches` (must fail on `code-v1` default cuts, pass after 1.1). Verify with `pytest -q tests/unit/test_code_chunker.py::test_figure_fixture_matches`.
- [x] 2.2 Add an e2e that syncs the figure as `processor.py` and checks `get processor.py --json` children titles against `figure.json`. Verify `pytest -q` on that test.
- [x] 2.3 Write ADR `docs/decisions/0010-code-block-children.md`, CHANGELOG Unreleased, evidence stub, and a PROGRESS row. Verify the ADR number is 0010 and does not duplicate 0009.

## 3. Gates

- [x] 3.1 Run `ruff check .`, `ruff format --check .`, `mypy --strict src`, `openspec validate fix-code-block-chunks --strict`, and `pytest -q --cov=src/lodestone --cov-fail-under=85`. Verify all pass.

## Workflow follow-up

- Ready PR, wait for 10/10 CI, local `--no-ff` merge, `openspec archive --yes --skip-specs` if main specs already synced, `ruff format` after archive, push main.
