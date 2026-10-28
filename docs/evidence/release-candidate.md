# BEIR adapter, MCP Docker image, and 0.1.0rc1 release prep

Feature base: `main` at `5bfe7f4`.
Branch: `feat/release-candidate`.
OpenSpec change: `add-release-candidate`.
Existing migrations were not edited.

Main at `5bfe7f4` push CI, including macOS, was already green:
https://github.com/drkwv34/lodestone-kb/actions/runs/40542688870

```text
$ gh run view 40542688870 --json conclusion,headSha,url,jobs
{"conclusion":"success","headSha":"5bfe7f48eb35227edeb0069a539305424e277372","url":"https://github.com/drkwv34/lodestone-kb/actions/runs/40542688870"}
```

Jobs on that run: lint-type, licenses, openspec, build, test Ubuntu 3.11/3.12/3.13, test macOS 3.12, Windows smoke — all success.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.15.0

$ openspec validate add-release-candidate --strict
Change 'add-release-candidate' is valid

$ openspec list
Changes:
  add-release-candidate     ✓ Complete
```

## Requirement checklist

- [x] FR-079: `test_fr_079_offline_fixture_imports_without_network`,
  `test_fr_079_checksum_mismatch_rejects`,
  `test_fr_079_local_zip_and_unknown_dataset`,
  `test_fr_079_download_with_matching_checksum`,
  `test_fr_079_network_download_is_opt_in` (deselected; `@pytest.mark.network`)
- [x] MCP image: `test_fr_mcp_dockerfile_entrypoint`
- [x] Version: `test_fr_version_cli_matches_package`
- [x] Findings: `test_nfr_benchmark_findings_not_run_needs_keys`
- [x] NFR-005 search JSON: `test_nfr_005_search_json_deterministic`
- [x] Decision: `docs/decisions/0008-release-candidate.md`

## Gates (local)

```text
$ ruff check .
All checks passed!

$ ruff format --check .
310 files already formatted

$ mypy --strict src
Success: no issues found in 93 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python scripts/check_modules.py
Module gate: 166 Python files <= 500 lines, all SPDX headers present

$ python scripts/check_links.py
Link check: 9 pages, internal targets exist
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
233 passed, 5 deselected in 40.36s
TOTAL                                             5877    477    92%
Required test coverage of 85% reached. Total coverage: 91.88%
```

## Demo

```text
$ lodestone --version
0.1.0rc1

$ lodestone bench import beir:scifact --from tests/fixtures/beir/scifact --out /tmp/lodestone-beir-demo
wrote 2 questions to /tmp/lodestone-beir-demo/evalset.jsonl
documents 2
```

## Docker build

Docker was not installed on the implementer machine (`command -v docker`
printed nothing). The Ubuntu CI `docker` job runs:

```yaml
run: |
  docker build -t lodestone-mcp:0.1.0rc1 .
```

No `docker push`. Transcript from that job is pasted under CI below once
the PR run finishes.

## FINDINGS H1–H5

See [docs/benchmarks/FINDINGS.md](../benchmarks/FINDINGS.md). All five are
**not tested**. The committed synth run used the hash embedder and omitted
`lodestone-hybrid`, decay pairing, and `full-context`. Real-embedder:
`status: not run - needs keys`.

## Requirements status (all M green)

| ID | Pri | Status | Proving test(s) |
|---|---|---|---|
| FR-001 | M | shipped | `test_fr_001_init_idempotence_smoke` |
| FR-002 | M | shipped | `test_fr_002_five_invalid_fixtures`, `test_fr_002_config_show_smoke` |
| FR-003 | M | shipped | `test_fr_003_project_scope_property_200_queries` |
| FR-004 | M | shipped | `test_fr_004_fr_003_fr_005_source_lifecycle_smoke` |
| FR-005 | S | shipped | `test_fr_005_secret_redaction_preview`, `test_fr_005_runtime_secret_overrides_redaction_and_no_persistence` |
| FR-010 | M | shipped | `test_fr_010_fixture_globs_gitignore_binary_oversize`, `test_fr_010_fr_030_fr_041_sync_search_smoke` |
| FR-011 | M | shipped | `test_fr_011_malformed_jsonl_reports_line_numbers`, `test_fr_011_fr_012_threads_sync_search_smoke` |
| FR-012 | M | shipped | `test_fr_012_thread_append_updates_in_place_and_removes_old_bursts` |
| FR-013 | M | shipped | `test_fr_013_cerebras_five_message_figure` |
| FR-014 | M | shipped | `test_fr_014_resync_zero_writes_and_single_file_edit` |
| FR-015 | M | shipped | `test_fr_015_heading_path_golden` |
| FR-016 | M | shipped | `test_fr_016_class_method_if_for_golden` |
| FR-017 | M | shipped | `test_fr_017_example_plugin_loads_through_entry_points` |
| FR-018 | S | shipped | `test_fr_018_ingest_concurrency_cap_under_429_500` |
| FR-020 | M | shipped | `test_fr_020_malformed_json_retry_then_valid` |
| FR-021 | M | shipped | `test_fr_021_golden_heuristic_cards` |
| FR-022 | M | shipped | `test_fr_022_norm_text_and_card_embed_input` |
| FR-023 | M | shipped | `test_fr_023_cache_hit_ratio_and_model_change` |
| FR-024 | M | shipped | `test_fr_024_provenance_and_get_record` |
| FR-025 | S | shipped | `test_fr_025_contextual_prefix_is_fts_matchable` |
| FR-026 | M | shipped | `test_fr_026_cost_totals_equal_sum_of_log_rows` |
| FR-030 | M | shipped | `test_fr_030_exact_token_ranks_first`, `test_fr_030_sanitiser_fuzz_1000_strings` |
| FR-031 | M | shipped | `test_fr_031_paraphrase_found_only_by_fts_card` |
| FR-032 | M | shipped | `test_fr_032_rare_lane_requires_rare_query_term` |
| FR-033 | S | shipped | `test_fr_033_backend_parity_1000_vectors` |
| FR-034 | M | shipped | `test_fr_034_grep_lane_and_regex_guard` |
| FR-035 | M | shipped | `test_fr_035_rrf_reproduces_cerebras_figure` |
| FR-036 | M | shipped | `test_fr_036_decay_orders_threads_and_respects_floor` |
| FR-037 | M | shipped | `test_fr_037_collapse_and_per_source_cap` |
| FR-038 | M | shipped | `test_fr_038_neighbour_expansion_edge_cases` |
| FR-039 | S | shipped | `test_fr_039_rerank_permutes_candidate_pool` |
| FR-040 | M | shipped | `test_fr_040_explain_contributions_sum_to_fused_score` |
| FR-041 | M | shipped | `test_fr_041_filters_property_500_combinations` |
| FR-042 | M | shipped | `test_fr_042_evidence_packet_schema` |
| FR-043 | S | shipped | `test_fr_043_who_knows_returns_expected_top_expert` |
| FR-044 | S | shipped | `test_fr_044_recent_deterministic_order` |
| FR-050 | M | shipped | `test_fr_050_sdk_mypy_strict`, `test_fr_050_readme_doctest` |
| FR-051 | M | shipped | `test_fr_051_cli_help_snapshots`, `test_fr_051_bench_commands` |
| FR-052 | M | shipped | `test_fr_052_mcp_tools_validate_against_schema` |
| FR-053 | M | shipped | `test_fr_053_citations_only_retrieved_ids` |
| FR-054 | M | shipped | `test_fr_054_planner_fallback_on_malformed_plan` |
| FR-055 | S | shipped | `test_fr_055_adversarial_sufficiency_terminates` |
| FR-056 | M | shipped | `test_fr_056_injection_payloads_do_not_alter_tools` |
| FR-060 | M | shipped | `test_fr_060_provider_fault_injection` |
| FR-061 | M | shipped | `test_fr_061_hash_embedder_deterministic` |
| FR-062 | M | shipped | `test_fr_062_offline_guard_hash_embedder_and_remote_raises` |
| FR-063 | M | shipped | `test_fr_063_scripted_and_rule_based_without_network` |
| FR-064 | S | shipped | `test_fr_064_provider_preset_snippets_validate` |
| FR-070 | M | shipped | `test_fr_070_evalset_validates` |
| FR-071 | M | shipped | `test_fr_071_synth_determinism` |
| FR-072 | M | shipped | `test_fr_072_leakage_filter` |
| FR-073 | M | shipped | `test_fr_073_strategies_run_offline_threads_60` |
| FR-074 | M | shipped | `test_fr_074_metric_goldens` |
| FR-075 | M | shipped | `test_fr_075_bootstrap_known_distribution` |
| FR-076 | M | shipped | `test_fr_076_report_golden_stable` |
| FR-077 | S | shipped | `test_fr_077_advise_r1` … `test_fr_077_advise_r4` |
| FR-078 | S | shipped | `test_fr_078_resume_zero_duplicate_llm_calls` |
| FR-079 | C | shipped | `test_fr_079_offline_fixture_imports_without_network` |
| FR-080 | M | shipped | `test_fr_080_disabled_fts5_reports_remediation` |
| FR-081 | M | shipped | `test_fr_081_default_query_log_stores_no_text` |
| FR-082 | M | shipped | `test_fr_082_migration_apply_schema_and_idempotence` |
| FR-083 | S | shipped | `test_fr_083_reindex_lanes_fts_vec_cards` |
| NFR-001 | — | shipped (perf opt-in) | `test_nfr_001_lexical_search_p95` |
| NFR-002 | — | partial | `test_nfr_002_heuristic_ingest_throughput`; below 200 rec/s, plan in decision 0006 |
| NFR-003 | — | shipped (perf opt-in) | `test_nfr_003_incremental_no_change_sync` |
| NFR-004 | — | shipped | `docs/benchmarks/scale.md` |
| NFR-005 | — | shipped | `test_nfr_005_search_json_deterministic`, `test_fr_076_report_golden_stable` |
| NFR-006 | — | shipped | `test_nfr_006_crash_injection_50_iterations` |
| NFR-007 | — | shipped | `test_nfr_007_provider_failures_degrade` |
| NFR-008 | — | shipped | `test_nfr_008_path_jail_and_log_scrub` |
| NFR-009 | — | shipped | `test_nfr_009_no_shell_rg_argument_arrays` |
| NFR-010 | — | shipped | `test_nfr_010_offline_zero_network` |
| NFR-011 | — | shipped | CI matrix (Ubuntu 3.11/3.12/3.13, macOS 3.12, Windows smoke) |
| NFR-012 | — | shipped | coverage 91.88%, mypy, ruff, module-size |
| NFR-013 | — | shipped | `test_nfr_013_quickstart_script_offline` |
| NFR-014 | — | shipped | `test_nfr_014_module_size_and_semver_policy` |
| NFR-015 | — | shipped | `test_nfr_015_json_logs_without_pii` |
| NFR-016 | — | shipped | `test_nfr_016_readme_and_docs_internal_links` |
| NFR-017 | — | shipped | `test_nfr_017_license_and_notice` plus CI licenses job |
| NFR-018 | — | partial | lower bounds in `pyproject.toml`; network marker in pytest; pip lockfile and Dependabot deferred in decision 0008 |

All **M** requirements are green.

## Authorship (filled after commits)

```text
$ git log 5bfe7f4..HEAD --format='%h %an <%ae> | %cn <%ce>'
# pasted after the feature commits land
```

## CI (PR head)

PR: (filled after open)
PR head SHA: (filled after push)
CI run URL: (filled after green)
conclusion: (filled after `gh run view`)
