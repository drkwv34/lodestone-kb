# Tasks

## 1. Plugins, concurrency, crash safety, and reindex

- [x] 1.1 Add entry-point connector loader and `examples/plugin_demo/` (<= 60
      lines); verify `test_fr_017_example_plugin_loads_through_entry_points`.
- [x] 1.2 Bound LLM ingest calls with `llm.max_concurrency` (default 4) on a
      worker pool; serialise SQLite writes; verify
      `test_fr_018_ingest_concurrency_cap_under_429_500`.
- [x] 1.3 Split ingest into a lexical transaction then a derived transaction;
      complete `pending` records on the next sync; verify
      `test_nfr_006_pending_derived_resumes_on_sync`.
- [x] 1.4 Add SIGKILL crash-injection harness (short default plus 50-iteration
      `slow` test); verify `test_nfr_006_crash_injection_sigkill`.
- [x] 1.5 Complete `reindex --lanes fts|vec|cards` from stored text; verify
      `test_fr_083_reindex_lanes_fts_vec_cards`.

## 2. Doctor, logging, security, offline, and degradation

- [x] 2.1 Complete `doctor` (sqlite-vec, provider reachability when configured
      and not offline) and `doctor --deep`; verify `test_fr_080_doctor_complete`
      and `test_nfr_006_doctor_deep_missing_fts`.
- [x] 2.2 Add JSON structured logs (`LODESTONE_LOG=json`), timing, and secret
      scrubbing; verify `test_nfr_015_json_logs_without_pii`.
- [x] 2.3 Add security tests for path jail, log scrubbing, no shell, and `rg`
      argv; verify `test_nfr_008_path_jail_and_log_scrub` and
      `test_nfr_009_no_shell_rg_argument_arrays`.
- [x] 2.4 Complete offline ingest+search+bench with sockets patched; verify
      `test_fr_062_offline_ingest_search_bench_socket_blocked` and
      `test_nfr_010_offline_zero_network`.
- [x] 2.5 Degrade provider faults (cards, rerank, vec, ask); verify
      `test_nfr_007_provider_failures_degrade`.
- [x] 2.6 Add privacy data-flow table and measured 200k lexical scale doc;
      verify `test_nfr_010_data_flow_table_present` and
      `docs/benchmarks/scale.md` with real numbers.

## 3. Contracts and gates

- [x] 3.1 Extend import-linter if new packages are added; keep modules <= 500
      lines and ruff `S` clean; verify `lint-imports`, `scripts/check_modules.py`,
      and `ruff check .`.
- [x] 3.2 Run `openspec validate add-hardening --strict`, mypy --strict, and
      pytest with coverage at least 85%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
- Paste real command output in `docs/evidence/hardening.md`.
