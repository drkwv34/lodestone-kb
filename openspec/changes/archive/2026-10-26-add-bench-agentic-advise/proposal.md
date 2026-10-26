# Proposal

## Why

Benchmark I shipped formats, a synthetic corpus, four baseline strategies, and
a report skeleton, but the remaining FR-073 strategies are skipped stubs and
there is no question-generation leakage filter, bootstrap statistics, advise
verdict, or resume cache. Teams still cannot compare Lodestone hybrid/rerank
and agentic/full-context runs against classic RAG on the same corpus, and an
interrupted run would re-spend tokens.

## What Changes

- Add real-corpus question generation (`lodestone bench generate`) with
  stratified sampling, FakeLLM questions, Jaccard leakage scoring, a
  `leakage_max` filter (default 0.5), category tags, and a leakage histogram
  on the report (FR-072).
- Implement remaining FR-073 strategies on isolated indexes with FakeLLM and
  the hash embedder only: `lodestone-hybrid`, `lodestone-rerank`,
  `agentic-ask`, `grep-agent`, and `full-context`. `full-context` reports
  `skipped: too_large` when the corpus exceeds `context_budget_tokens`.
- Extend FR-074 with answer correctness (`must_contain` substring match) and
  optional `--judge` (FakeLLM in tests).
- Add 95% bootstrap CIs (2,000 resamples, seeded) and paired bootstrap
  differences vs `classic-rag` with a `significant` flag (FR-075).
- Add `lodestone bench advise` with deterministic rules R1–R4 (FR-077).
- Add a resume cache keyed by `(strategy, config hash, corpus hash, qid)` so
  an interrupted run performs zero duplicate LLM calls (FR-078).
- Fill report leakage stats and attach CIs / paired diffs; keep the hash
  embedder caveat.

## Capabilities

### New Capabilities

- `bench-agentic-advise`: remaining RAG-strategy implementations, question
  generation with leakage, correctness/judge, bootstrap statistics, advise
  rules R1–R4, and the bench resume cache.

### Modified Capabilities

- `bench-formats-synth`: FR-073 skipped stubs for `lodestone-hybrid`,
  `lodestone-rerank`, `agentic-ask`, `grep-agent`, and `full-context` are
  replaced by the implementations in this change; unimplemented names are
  still reported as skipped when they occur. FR-076 leakage is no longer an
  empty placeholder once questions are generated.

## Impact

New modules under `lodestone.bench` (`questions`, `stats`, `advise`, `cache`)
and strategy files `grep_agent.py`, `full_context.py`, `agentic.py`;
`lodestone-hybrid` / `lodestone-rerank` extend the existing Lodestone
workspace strategy. CLI gains `bench generate` and `bench advise`. Runner
gains correctness, optional judge, bootstrap, and resume. No schema
migration. Storage, lanes, fusion, rerank, providers, MCP, and ask are
reused, not rewritten. Tests stay offline (FakeLLM / hash embedder). Coverage
gate stays 85%.
