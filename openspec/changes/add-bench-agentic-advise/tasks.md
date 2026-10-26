# Tasks

## 1. Questions, stats, correctness, and cache

- [x] 1.1 Add `lodestone.bench.questions` (stratified sample, 1-3 questions per
      record, Jaccard leakage, `leakage_max` default 0.5, category tags,
      histogram); verify `test_fr_072_leakage_filter`.
- [x] 1.2 Add `lodestone.bench.stats` (95% percentile bootstrap, 2,000
      resamples, seeded; paired diffs vs `classic-rag` with `significant`);
      verify `test_fr_075_bootstrap_known_distribution` and
      `test_fr_075_paired_significance_flag`.
- [x] 1.3 Extend `lodestone.bench.metrics` with `must_contain` correctness and
      optional FakeLLM judge; verify `test_fr_074_must_contain_correctness`
      and `test_fr_074_optional_judge`.
- [x] 1.4 Add `lodestone.bench.cache` keyed by strategy, config hash, corpus
      hash, and qid; verify `test_fr_078_resume_zero_duplicate_llm_calls`.

## 2. Remaining strategies, advise, runner, and report

- [x] 2.1 Implement `lodestone-hybrid` and `lodestone-rerank` on isolated
      workspaces (hash embedder, FakeLLM rerank); verify they run offline in
      `test_fr_073_remaining_strategies_run_offline`.
- [x] 2.2 Implement `agentic-ask` (ask pipeline; retrieve = cited evidence
      union) and `grep-agent` (grep/read tools, max 8 calls) with FakeLLM;
      verify in `test_fr_073_remaining_strategies_run_offline`.
- [x] 2.3 Implement `full-context` with `context_budget_tokens`; verify
      `test_fr_073_full_context_skipped_too_large`.
- [x] 2.4 Add `lodestone.bench.advise` rules R1-R4 with evidence lines;
      verify `test_fr_077_advise_r1` through `test_fr_077_advise_r4`.
- [x] 2.5 Wire runner resume cache, correctness/judge, bootstrap CIs, paired
      diffs, and leakage into `report.v1`; verify skipped strategies still
      appear and the hash-embedder caveat remains.

## 3. CLI, contracts, and gates

- [x] 3.1 Add `lodestone bench generate` and `lodestone bench advise`; extend
      `run` with `--judge`, `--reps`, and `--context-budget`; verify
      `test_fr_051_bench_commands` still passes and generate/advise appear in
      help.
- [x] 3.2 Run `openspec validate add-bench-agentic-advise --strict`, ruff,
      mypy --strict, import-linter, module-size gate, and pytest with coverage
      at least 85%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
- Do not invent benchmark numbers; paste real command output in
  `docs/evidence/bench-agentic-advise.md`.
