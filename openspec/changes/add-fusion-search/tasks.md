# Tasks

## 1. Fusion primitives

- [x] 1.1 Add `lodestone.fusion` (RRF, decay, collapse, expand) and extend import-linter so fusion sits with lanes; verify `test_fr_035_rrf_reproduces_cerebras_figure`.
- [x] 1.2 Apply recency decay with floor, future-timestamp clamp and `--no-decay`; verify `test_fr_036_decay_orders_threads_and_respects_floor`.
- [x] 1.3 Collapse same-parent hits with matched children and apply per-source cap inside the candidate pool; verify `test_fr_037_collapse_and_per_source_cap`.
- [x] 1.4 Expand chunk/section neighbours including first, last and missing siblings within `expand_max_chars`; verify `test_fr_038_neighbour_expansion_edge_cases`.

## 2. Grep, filters and evidence

- [x] 2.1 Add `lanes/grep.py` with literal/regex scan, line context, length and nested-quantifier guards and a 2 s budget; verify `test_fr_034_grep_lane_and_regex_guard`.
- [x] 2.2 Complete FR-041 filters (project, source, kind, author, since, until, metadata) on every lane before fusion; verify `test_fr_041_filters_property_500_combinations`.
- [x] 2.3 Add `schemas/evidence.v1.json` plus packet models and `search --explain`; verify `test_fr_040_explain_contributions_sum_to_fused_score` and `test_fr_042_evidence_packet_schema`.

## 3. Pipeline, CLI and perf

- [x] 3.1 Orchestrate FTS, optional vec and opt-in grep through weighted RRF fusion as the default search when `--lane` is omitted; verify fused CLI/e2e output includes per-lane contributions.
- [x] 3.2 Add `tests/perf/` for NFR-001 p95, NFR-002 ingest throughput and NFR-003 no-change sync on 20,000 records, excluded from the default run; verify `test_nfr_001_lexical_search_p95`, `test_nfr_002_heuristic_ingest_throughput` and `test_nfr_003_incremental_no_change_sync` print measured numbers.

## 4. Integration checks

- [x] 4.1 Run `openspec validate add-fusion-search --strict`, ruff, mypy --strict, import-linter, module-size gate, and pytest with coverage >= 80%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
