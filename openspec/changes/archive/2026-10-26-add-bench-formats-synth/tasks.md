# Tasks

## 1. Formats, window chunker, and metrics

- [x] 1.1 Add `schemas/evalset.v1.json` and `lodestone.bench.evalset` loader
      that rejects invalid JSONL with 1-based line numbers; verify
      `test_fr_070_evalset_validates` and `test_fr_070_invalid_rows_report_line_numbers`.
- [x] 1.2 Add `chunking/window.py` (512 tokens, overlap 64) using `tokenize()`;
      verify `test_fr_073_window_overlap_512_64`.
- [x] 1.3 Add `lodestone.bench.metrics` with recall@{1,5,10,20}, MRR, nDCG@10,
      parent collapse, cost USD, and latency percentiles; verify
      `test_fr_074_metric_goldens` and `test_fr_074_parent_collapse`.

## 2. Synth, strategies, runner, and report

- [x] 2.1 Implement `lodestone.bench.synth` (`--seed`, `--threads`) emitting
      threads, docs, code, and evalset for all six categories, byte-identical
      for the same seed; verify `test_fr_071_synth_determinism` (pinned hash)
      and `test_fr_071_synth_categories`.
- [x] 2.2 Implement strategy interface plus `classic-rag`, `bm25-chunks`,
      `hybrid-chunks`, and `lodestone-lexical` on isolated DBs with hash
      embedder / heuristic cards; verify
      `test_fr_073_strategies_run_offline_threads_60`.
- [x] 2.3 Register remaining strategies as skipped stubs (`lodestone-hybrid`,
      `lodestone-rerank`, `agentic-ask`, `grep-agent`, `full-context` — not in
      this change) and verify `test_fr_073_skipped_strategies_reported`.
- [x] 2.4 Implement runner and `report.v1` markdown/JSON skeleton with hashes,
      tables, leakage placeholder, caveats, and failures; verify
      `test_fr_076_hash_embedder_caveat` and `test_fr_076_report_golden_stable`.

## 3. CLI, contracts, and gates

- [x] 3.1 Add `lodestone bench synth|run|report`, extend import-linter so
      `bench` sits beside `sdk` above `workspace`, and include schemas in the
      wheel; verify `test_fr_051_bench_commands` and `test_fr_070_run_validates_evalset`.
- [x] 3.2 Run `openspec validate add-bench-formats-synth --strict`, ruff,
      mypy --strict, import-linter, module-size gate, and pytest with coverage
      at least 85%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
- `lodestone-hybrid`, `lodestone-rerank`, `agentic-ask`, `grep-agent`, and
  `full-context` are not in this change (skipped stubs only).
- FR-072, FR-075, FR-077, FR-078, and answer correctness / LLM-judge are not
  in this change.
