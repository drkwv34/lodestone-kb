# Plugin loader, crash safety, security hardening, and doctor --deep

Feature base: `main` at `181b097`.
Branch: `feat/hardening`.
OpenSpec change: `add-hardening`.
Existing migrations were not edited. Schema version remains 3.

Implements FR-017 (entry-point connectors + `examples/plugin_demo/`), FR-018
(bounded ingest concurrency), complete FR-062 (offline ingest+search+bench),
complete FR-080 (`doctor` sqlite-vec/provider/`--deep`), complete FR-083
(`reindex --lanes fts|vec|cards`), NFR-004 (measured 200k lexical scale),
NFR-006 (two-phase ingest, SIGKILL harness, `doctor --deep`), NFR-007
(provider degradation), NFR-008/NFR-009 (path jail, log scrubbing, no shell,
`rg` argv, ruff `S`), NFR-010 (offline zero network + privacy data-flow
table), and NFR-015 (JSON logs, timing, secret scrubbing).

Main at `181b097` push CI, including macOS, was already green:
https://github.com/drkwv34/lodestone-kb/actions/runs/40355558375

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.15.0

$ openspec validate add-hardening --strict
Change 'add-hardening' is valid

$ openspec validate --all --strict
✓ change/add-hardening
✓ spec/bench-agentic-advise
✓ spec/bench-formats-synth
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/lexical-search
✓ spec/mcp-ask
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 13 passed, 0 failed (13 items)

$ openspec list
Changes:
  add-hardening     ✓ Complete
```

## Requirement checklist

- [x] FR-017: `test_fr_017_example_plugin_loads_through_entry_points`
- [x] FR-018: `test_fr_018_ingest_concurrency_cap_under_429_500`
- [x] FR-062 complete: `test_fr_062_offline_ingest_search_bench_socket_blocked`
- [x] FR-080 complete: `test_fr_080_doctor_complete`
- [x] FR-083 complete: `test_fr_083_reindex_lanes_fts_vec_cards`
- [x] NFR-004: `docs/benchmarks/scale.md` (measured, not invented)
- [x] NFR-006: `test_nfr_006_crash_injection_sigkill`, `test_nfr_006_crash_injection_50_iterations`, `test_nfr_006_pending_derived_resumes_on_sync`, `test_nfr_006_doctor_deep_missing_fts`
- [x] NFR-007: `test_nfr_007_provider_failures_degrade`
- [x] NFR-008: `test_nfr_008_path_jail_and_log_scrub`
- [x] NFR-009: `test_nfr_009_no_shell_rg_argument_arrays`
- [x] NFR-010: `test_nfr_010_offline_zero_network`, `test_nfr_010_data_flow_table_present`
- [x] NFR-015: `test_nfr_015_json_logs_without_pii`

## Gates (local)

```text
$ ruff check .
All checks passed!

$ ruff format --check .
279 files already formatted

$ mypy --strict src
Success: no issues found in 92 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 162 Python files <= 500 lines, all SPDX headers present
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
220 passed, 4 deselected in 40.29s
TOTAL                                             5668    442    92%
Required test coverage of 85% reached. Total coverage: 92.20%
```

## Crash-injection (NFR-006)

Default matrix: `test_nfr_006_crash_injection_sigkill` (3 workspaces).
Opt-in 50-iteration harness:

```text
$ pytest -q tests/integration/test_crash.py -m slow --tb=short
.                                                                        [100%]
1 passed, 1 deselected in 14.24s
```

50/50 recovered databases had an FTS row for every non-tombstoned record
(`deep_errors` empty).

## Scale run (NFR-004)

See [benchmarks/scale.md](../benchmarks/scale.md). Hardware: Linux 6.12.94+
x86_64, Intel Xeon, 4 CPUs, ~15.6 GiB RAM, Python 3.12.3, SQLite 3.45.1.

```text
$ LODESTONE_SCALE_N=200000 python3 scripts/scale_lexical.py
records=200000
insert_s=4.73
db_bytes=146984960
db_gb=0.1369
search_ms=19.16
search_hits=10
rss_mb=54.1
```

## `lodestone doctor --deep`

```text
$ lodestone doctor --deep --offline --config /tmp/lodestone-doctor-HzBY/lodestone.toml
Python: 3.12.3
SQLite: 3.45.1
FTS5: available (identifier tokenizer probe passed)
sqlite-vec: available
Database schema: 3 (supported: 3)
Provider: skipped (offline or unconfigured)
Deep: FTS, term_stats, embeddings, and orphans OK
Doctor: OK (deep checks passed)
```

## Authorship (feature branch, before merge)

```text
$ git log 181b097..HEAD --format='%h %an <%ae> | %cn <%ce>'
# filled after commits land on feat/hardening

$ git log 181b097..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## CI (PR head)

PR: (filled after open)
PR head SHA: (filled after push)
CI run URL: (filled after green)
conclusion: (filled after green, including macOS)

## Merge and archive

Filled after local `--no-ff` merge, archive commit on main, and main push CI.
