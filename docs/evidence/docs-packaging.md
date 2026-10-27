# User guides, quickstart, and verified wheel packaging

Feature base: `main` at `ab012da`.
Branch: `feat/docs-packaging`.
OpenSpec change: `add-docs-packaging`.
Existing migrations were not edited. Schema version remains 3.

Implements NFR-013 (`examples/quickstart.sh` offline in CI), NFR-016 (user
guides + internal link check), NFR-014 (semver/deprecation policy + 500-line
module lint), FR-064 (Cerebras/OpenAI/Ollama snippets still validated by
`test_fr_064_provider_preset_snippets_validate`), verified wheel+sdist install
into a clean venv, and honest `docs/benchmarks/FINDINGS.md`. FR-078 already
shipped as `test_fr_078_resume_zero_duplicate_llm_calls`; it was not
reimplemented.

Main at `ab012da` push CI, including macOS, was already green:
https://github.com/drkwv34/lodestone-kb/actions/runs/40363604422

```text
$ gh run view 40363604422 --json conclusion,headSha,url
{"conclusion":"success","headSha":"ab012dae2382b555c85e1f9e7ea7952c27a77762","url":"https://github.com/drkwv34/lodestone-kb/actions/runs/40363604422"}
```

Jobs on that run: lint-type, licenses, openspec, build, test Ubuntu 3.11/3.12/3.13, test macOS 3.12, Windows smoke — all success.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.15.0

$ openspec validate add-docs-packaging --strict
Change 'add-docs-packaging' is valid

$ openspec validate --all --strict
✓ change/add-docs-packaging
✓ spec/bench-agentic-advise
✓ spec/bench-formats-synth
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/hardening
✓ spec/lexical-search
✓ spec/mcp-ask
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 14 passed, 0 failed (14 items)

$ openspec list
Changes:
  add-docs-packaging     ✓ Complete
```

## Requirement checklist

- [x] NFR-013: `test_nfr_013_quickstart_script_offline`
- [x] NFR-016: `test_nfr_016_readme_and_docs_internal_links`
- [x] NFR-014: `test_nfr_014_module_size_and_semver_policy`
- [x] FR-064: `test_fr_064_provider_preset_snippets_validate`
- [x] FR-078 (already shipped): `test_fr_078_resume_zero_duplicate_llm_calls`
- [x] Wheel smoke: `test_wheel_smoke_cli` plus CI clean-venv `pip install dist/*.whl`
- [x] Findings: `test_nfr_benchmark_findings_not_run_needs_keys`

## Gates (local)

```text
$ ruff check .
All checks passed!

$ ruff format --check .
298 files already formatted

$ mypy --strict src
Success: no issues found in 92 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 164 Python files <= 500 lines, all SPDX headers present

$ python3 scripts/check_links.py
Link check: 8 pages, internal targets exist
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
226 passed, 4 deselected in 45.74s
TOTAL                                             5668    442    92%
Required test coverage of 85% reached. Total coverage: 92.20%
```

## `examples/quickstart.sh`

```text
$ bash examples/quickstart.sh
Initialised lodestone.toml and database schema 3
Added source: docs
INFO op complete
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 1, "cards_llm": 0, "cards_heuristic": 1, "max_concurrency": 1}
1. docs/manifest.md [doc] (fts_raw, 0.049180)
   explain: fts_raw r=1 c=0.0164 fts_card r=1 c=0.0164 vec_card r=1 c=0.0164 decay=1.0 final=0.04918032786885246
   # Manifest restore
[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.
```

## Clean-venv `pip install dist/*.whl`

```text
$ python3 -m build
Successfully built lodestone_kb-0.1.0.dev0.tar.gz and lodestone_kb-0.1.0.dev0-py3-none-any.whl

$ python3 -m virtualenv /tmp/lodestone-wheel-clean
created virtual environment CPython3.12.3.final.0-64-x86_64 in 166ms

$ /tmp/lodestone-wheel-clean/bin/pip install dist/*.whl
...
Successfully installed ... lodestone-kb-0.1.0.dev0 ...

$ /tmp/lodestone-wheel-clean/bin/python scripts/smoke_wheel.py
Initialised lodestone.toml and database schema 3
...
Added source: wiki
INFO op complete
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 1, "cards_llm": 0, "cards_heuristic": 1, "max_concurrency": 1}
Wheel smoke: init, doctor, config, sync, fused search passed
```

## CI YAML fix

Push CI on `2cc17bb` failed with zero jobs (invalid workflow YAML around
`.github/workflows/ci.yml` L85): `run:` values that started with
`"$RUNNER_TEMP/..."` were parsed as quoted scalars. The clean-venv
`pip install dist/*.whl` steps are unchanged; they are now YAML block
scalars. Failed run:
https://github.com/drkwv34/lodestone-kb/actions/runs/40539871520

## CI (PR head)

PR: https://github.com/drkwv34/lodestone-kb/pull/16
PR head SHA: `b5ddd5c1b6247a849fbfe2987560634cb670ebea`
CI run URL: https://github.com/drkwv34/lodestone-kb/actions/runs/40540708667
conclusion: success (including macOS)

```text
$ gh run view 40540708667 --json conclusion,headSha,url,status
{"conclusion":"success","headSha":"b5ddd5c1b6247a849fbfe2987560634cb670ebea","status":"completed","url":"https://github.com/drkwv34/lodestone-kb/actions/runs/40540708667"}

$ gh run view 40540708667

✓ feat/docs-packaging ci drkwv34/lodestone-kb#16 · 40540708667
Triggered via pull_request about 4 minutes ago

JOBS
✓ build in 35s (ID 122318000046)
✓ lint-type in 36s (ID 122318000372)
✓ openspec in 15s (ID 122318000587)
✓ licenses in 21s (ID 122318000815)
✓ test (ubuntu-latest, 3.11) in 1m30s (ID 122318372493)
✓ test (macos-latest, 3.12) in 2m22s (ID 122318372509)
✓ test (ubuntu-latest, 3.13) in 1m32s (ID 122318372565)
✓ test (ubuntu-latest, 3.12) in 1m36s (ID 122318372642)
✓ test (windows-latest, 3.12, true) in 1m8s (ID 122318372654)
```

## Authorship

```text
$ git log ab012da..HEAD --format='%h %an <%ae> | %cn <%ce>'
4f55d69 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
b5ddd5c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
2cc17bb Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9e728f5 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
b7e4bae Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
c1a8a90 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log ab012da..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Merge and archive

Merge commit: `4f55d69e96bebe88409fed3e8733b06e9e3cfe77`. Author and committer
are Christian Agila <87576768+drkwv34@users.noreply.github.com>. Two parents
(`ab012da` and `b5ddd5c`). No co-author trailers.

```text
$ git log -1 --format='%H%n%h %an <%ae> | %cn <%ce>%n%B'
4f55d69e96bebe88409fed3e8733b06e9e3cfe77
4f55d69 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
Merge pull request #16 from drkwv34/feat/docs-packaging

docs: user guides, quickstart, and verified wheel packaging
```

OpenSpec archived as `2026-10-27-add-docs-packaging` on main. Specs synced
(new `docs-packaging` main spec).

```text
$ openspec validate --all --strict
✓ spec/bench-agentic-advise
✓ spec/bench-formats-synth
✓ spec/chunkers-sources
✓ spec/docs-packaging
✓ spec/fusion-search
✓ spec/hardening
✓ spec/lexical-search
✓ spec/mcp-ask
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 14 passed, 0 failed (14 items)

$ openspec list
No active changes found.
```

Main push CI on the archive commit (including macOS) will be pasted after that
run completes.
