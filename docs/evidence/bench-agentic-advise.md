# Bench agentic strategies, stats, and advise

Feature base: `main` at `349062d`.
Branch: `feat/bench-agentic-advise`.
OpenSpec change: `add-bench-agentic-advise`.
Existing migrations were not edited. Schema version remains 3.

Implements FR-072, remaining FR-073 strategies (`lodestone-hybrid`,
`lodestone-rerank`, `agentic-ask`, `grep-agent`, `full-context`), FR-074
correctness and optional judge, FR-075 bootstrap CIs and paired diffs,
FR-077 advise rules R1-R4, and FR-078 resume cache. Offline FakeLLM and
hash embedder only.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.15.0

$ openspec validate add-bench-agentic-advise --strict
Change 'add-bench-agentic-advise' is valid

$ openspec validate --all --strict
✓ change/add-bench-agentic-advise
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
Totals: 12 passed, 0 failed (12 items)

$ openspec list
Changes:
  add-bench-agentic-advise     ✓ Complete
```

## Requirement checklist

- [x] FR-072: `test_fr_072_leakage_filter`, `test_fr_072_generate_from_workspace`
- [x] FR-073 remaining: `test_fr_073_remaining_strategies_run_offline`, `test_fr_073_full_context_skipped_too_large`, `test_fr_073_skipped_strategies_reported`
- [x] FR-074 correctness: `test_fr_074_must_contain_correctness`, `test_fr_074_optional_judge`
- [x] FR-075: `test_fr_075_bootstrap_known_distribution`, `test_fr_075_paired_significance_flag`
- [x] FR-077: `test_fr_077_advise_r1`, `test_fr_077_advise_r2`, `test_fr_077_advise_r3`, `test_fr_077_advise_r4`
- [x] FR-078: `test_fr_078_resume_zero_duplicate_llm_calls`
- [x] FR-051 bench: `test_fr_051_bench_commands`

## Gates (local)

```text
$ ruff check .
All checks passed!

$ ruff format --check .
250 files already formatted

$ mypy --strict src
Success: no issues found in 83 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 144 Python files <= 500 lines, all SPDX headers present
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
205 passed, 3 deselected in 33.77s
TOTAL                                             5313    418    92%
Required test coverage of 85% reached. Total coverage: 92.13%
```

## Offline bench transcript

Synthetic corpus `--seed 42 --threads 6`, all nine strategies, FakeLLM and
hash embedder, `--context-budget 1000000`. Timed locally; do not treat
hash-embedder recall as semantic quality.

```text
$ lodestone bench synth --seed 42 --threads 6 --out /tmp/lodestone-bench-ii/corpus
wrote 6 questions to /tmp/lodestone-bench-ii/corpus/evalset.jsonl
corpus_hash 7a82f79dee55a86f6717456df2592958cbdffc97f3b7512606366de687fa3053
elapsed 0.317 seconds

$ lodestone bench run --corpus /tmp/lodestone-bench-ii/corpus --out /tmp/lodestone-bench-ii/run --k 10 --strategies all --context-budget 1000000
wrote /tmp/lodestone-bench-ii/run/report.md
elapsed 1.412 seconds

$ lodestone bench advise /tmp/lodestone-bench-ii/run
verdict: embeddings do not pay for themselves on this corpus
rule: R1
evidence:
- lodestone-lexical recall@10=1.0000
- best embedding classic-rag recall@10=1.0000
- |delta|=0.0000 pp-limit=0.03
- paired CI includes 0: True lo=0.0 hi=0.0
elapsed 0.287 seconds

===== total elapsed 2.015 seconds =====
```

Report excerpt (hash-embedder caveat required; numbers are machinery-only):

```text
# Lodestone bench report
Generated: 2026-10-26T15:35:02+00:00

## Run
- config_hash: 0ad42a0aa7b87db2aa95de5f6d32de82625c8a3330c786c4b66217dadf9ca3c9
- corpus_hash: 7a82f79dee55a86f6717456df2592958cbdffc97f3b7512606366de687fa3053
- lodestone: 0.1.0.dev0
- embedder: hash

## Strategies
| strategy | status | recall@1 | recall@5 | recall@10 | recall@20 | mrr | ndcg@10 | index_s | index_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic-rag | ok | 0.250000 | 0.833333 | 1.000000 | 1.000000 | 0.348810 | 0.463632 | 0.087951 | 45056 |
| bm25-chunks | ok | 0.250000 | 1.000000 | 1.000000 | 1.000000 | 0.430556 | 0.532089 | 0.015263 | 53248 |
| hybrid-chunks | ok | 0.250000 | 1.000000 | 1.000000 | 1.000000 | 0.416667 | 0.521822 | 0.020533 | 77824 |
| lodestone-lexical | ok | 0.583333 | 0.833333 | 1.000000 | 1.000000 | 0.607143 | 0.635768 | 0.092534 | 229376 |
| lodestone-hybrid | ok | 0.416667 | 0.833333 | 1.000000 | 1.000000 | 0.523810 | 0.574256 | 0.087922 | 229376 |
| lodestone-rerank | ok | 0.416667 | 0.833333 | 1.000000 | 1.000000 | 0.523810 | 0.574256 | 0.073166 | 229376 |
| agentic-ask | ok | 0.416667 | 0.833333 | 0.833333 | 0.833333 | 0.500000 | 0.518701 | 0.083612 | 229376 |
| grep-agent | ok | 0.333333 | 0.750000 | 0.833333 | 0.833333 | 0.338889 | 0.423794 | 0.001715 | 5320 |
| full-context | ok | 0.166667 | 0.750000 | 0.916667 | 0.916667 | 0.230556 | 0.345153 | 0.002400 | 5551 |

## Caveats
- hash embedder is not semantic
- leakage stats are a placeholder until real-corpus question generation
```

## CI (PR head)

PR and CI URLs will be pasted after the pull request is opened and the
macOS job is green.

## Authorship (feature range)

Recorded after merge. Zero `Co-authored-by` / `cursor[bot]` trailers.
