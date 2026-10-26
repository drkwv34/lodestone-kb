# Bench formats, synth corpus, baseline strategies

Feature base: `main` at `1ca12ba`.
Branch: `feat/bench-formats-synth`.
OpenSpec change: `add-bench-formats-synth`.
Existing migrations were not edited. Schema version remains 3.

Implements FR-070, FR-071, FR-073 (`classic-rag`, `bm25-chunks`,
`hybrid-chunks`, `lodestone-lexical`), FR-074 (retrieval + cost + latency),
FR-076 (report skeleton), and `chunking/window.py`. Remaining FR-073
strategies are skipped stubs. FR-072, FR-075, FR-077, FR-078, and answer
correctness / LLM-judge are not in this change.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.15.0

$ openspec validate add-bench-formats-synth --strict
Change 'add-bench-formats-synth' is valid

$ openspec validate --all --strict
✓ change/add-bench-formats-synth
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
Totals: 11 passed, 0 failed (11 items)

$ openspec list
Changes:
  add-bench-formats-synth     ✓ Complete
```

## Requirement checklist

- [x] FR-070: `test_fr_070_evalset_validates`, `test_fr_070_invalid_rows_report_line_numbers`, `test_fr_070_run_validates_evalset`
- [x] FR-071: `test_fr_071_synth_determinism`, `test_fr_071_synth_categories`
- [x] FR-073: `test_fr_073_window_overlap_512_64`, `test_fr_073_strategies_run_offline_threads_60`, `test_fr_073_skipped_strategies_reported`
- [x] FR-074: `test_fr_074_metric_goldens`, `test_fr_074_parent_collapse`
- [x] FR-076: `test_fr_076_hash_embedder_caveat`, `test_fr_076_report_golden_stable`
- [x] FR-051 bench: `test_fr_051_bench_commands`

## Authorship (feature range)

```text
$ git log 1ca12ba..HEAD --format='%h %an <%ae> | %cn <%ce>'
a51f898 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
389b0e8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
77ac466 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
d13a321 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
36681cb Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log 1ca12ba..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
192 passed, 3 deselected in 28.65s
TOTAL                                          4437    306    93%
Required test coverage of 85% reached. Total coverage: 93.10%
```

## CI

PR: https://github.com/drkwv34/lodestone-kb/pull/13

CI run URL pending GitHub Actions on this branch.

## Offline demo (`lodestone bench synth|run`)

```text
$ lodestone bench synth --seed 42 --threads 6 --out /tmp/bench-demo/corpus
wrote 6 questions to /tmp/bench-demo/corpus/evalset.jsonl
corpus_hash 7a82f79dee55a86f6717456df2592958cbdffc97f3b7512606366de687fa3053

$ lodestone bench run --corpus /tmp/bench-demo/corpus --out /tmp/bench-demo/run --k 10
wrote /tmp/bench-demo/run/report.md
```

Generated `report.md` (hash-embedder caveat visible):

```text
# Lodestone bench report
Generated: 2026-10-26T14:59:39+00:00

## Run
- config_hash: 01c4b0ec22bb668f2aff992f83cd3b14e2d249c857c9dc98101e2a4a67c7f867
- corpus_hash: 7a82f79dee55a86f6717456df2592958cbdffc97f3b7512606366de687fa3053
- lodestone: 0.1.0.dev0
- embedder: hash

## Strategies
| strategy | status | recall@1 | recall@5 | recall@10 | recall@20 | mrr | ndcg@10 | index_s | index_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic-rag | ok | 0.250000 | 0.833333 | 1.000000 | 1.000000 | 0.348810 | 0.463632 | 0.063844 | 45056 |
| bm25-chunks | ok | 0.250000 | 1.000000 | 1.000000 | 1.000000 | 0.430556 | 0.532089 | 0.015554 | 53248 |
| hybrid-chunks | ok | 0.250000 | 1.000000 | 1.000000 | 1.000000 | 0.416667 | 0.521822 | 0.020253 | 77824 |
| lodestone-lexical | ok | 0.583333 | 0.833333 | 1.000000 | 1.000000 | 0.607143 | 0.635768 | 0.126327 | 229376 |
| lodestone-hybrid | skipped |  |  |  |  |  |  | 0.000000 | 0 |
| lodestone-rerank | skipped |  |  |  |  |  |  | 0.000000 | 0 |
| agentic-ask | skipped |  |  |  |  |  |  | 0.000000 | 0 |
| grep-agent | skipped |  |  |  |  |  |  | 0.000000 | 0 |
| full-context | skipped |  |  |  |  |  |  | 0.000000 | 0 |

## Per category
| strategy | category | recall@10 | mrr | ndcg@10 |
| --- | --- | --- | --- | --- |
| classic-rag | exact_token | 1.000000 | 0.500000 | 0.630930 |
| classic-rag | paraphrase | 1.000000 | 0.142857 | 0.333333 |
| classic-rag | stale_vs_fresh | 1.000000 | 0.250000 | 0.430677 |
| classic-rag | tangent_in_long_thread | 1.000000 | 0.200000 | 0.386853 |
| classic-rag | multi_source | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| bm25-chunks | exact_token | 1.000000 | 0.500000 | 0.630930 |
| bm25-chunks | paraphrase | 1.000000 | 0.500000 | 0.630930 |
| bm25-chunks | stale_vs_fresh | 1.000000 | 0.333333 | 0.500000 |
| bm25-chunks | tangent_in_long_thread | 1.000000 | 0.250000 | 0.430677 |
| bm25-chunks | multi_source | 1.000000 | 1.000000 | 1.000000 |
| bm25-chunks | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| hybrid-chunks | exact_token | 1.000000 | 0.500000 | 0.630930 |
| hybrid-chunks | paraphrase | 1.000000 | 0.333333 | 0.500000 |
| hybrid-chunks | stale_vs_fresh | 1.000000 | 0.333333 | 0.500000 |
| hybrid-chunks | tangent_in_long_thread | 1.000000 | 0.333333 | 0.500000 |
| hybrid-chunks | multi_source | 1.000000 | 1.000000 | 1.000000 |
| hybrid-chunks | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| lodestone-lexical | exact_token | 1.000000 | 1.000000 | 1.000000 |
| lodestone-lexical | paraphrase | 1.000000 | 1.000000 | 1.000000 |
| lodestone-lexical | stale_vs_fresh | 1.000000 | 0.500000 | 0.630930 |
| lodestone-lexical | tangent_in_long_thread | 1.000000 | 0.142857 | 0.333333 |
| lodestone-lexical | multi_source | 1.000000 | 1.000000 | 0.850345 |
| lodestone-lexical | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| lodestone-hybrid | exact_token |  |  |  |
| lodestone-hybrid | paraphrase |  |  |  |
| lodestone-hybrid | stale_vs_fresh |  |  |  |
| lodestone-hybrid | tangent_in_long_thread |  |  |  |
| lodestone-hybrid | multi_source |  |  |  |
| lodestone-hybrid | unanswerable |  |  |  |
| lodestone-rerank | exact_token |  |  |  |
| lodestone-rerank | paraphrase |  |  |  |
| lodestone-rerank | stale_vs_fresh |  |  |  |
| lodestone-rerank | tangent_in_long_thread |  |  |  |
| lodestone-rerank | multi_source |  |  |  |
| lodestone-rerank | unanswerable |  |  |  |
| agentic-ask | exact_token |  |  |  |
| agentic-ask | paraphrase |  |  |  |
| agentic-ask | stale_vs_fresh |  |  |  |
| agentic-ask | tangent_in_long_thread |  |  |  |
| agentic-ask | multi_source |  |  |  |
| agentic-ask | unanswerable |  |  |  |
| grep-agent | exact_token |  |  |  |
| grep-agent | paraphrase |  |  |  |
| grep-agent | stale_vs_fresh |  |  |  |
| grep-agent | tangent_in_long_thread |  |  |  |
| grep-agent | multi_source |  |  |  |
| grep-agent | unanswerable |  |  |  |
| full-context | exact_token |  |  |  |
| full-context | paraphrase |  |  |  |
| full-context | stale_vs_fresh |  |  |  |
| full-context | tangent_in_long_thread |  |  |  |
| full-context | multi_source |  |  |  |
| full-context | unanswerable |  |  |  |

## Cost and latency
| strategy | in_tokens | out_tokens | usd | p50_ms | p95_ms | p99_ms |
| --- | --- | --- | --- | --- | --- | --- |
| classic-rag | 862 | 0 | 0.000000 | 0.348213 | 0.536037 | 0.566731 |
| bm25-chunks | 862 | 0 | 0.000000 | 1.913270 | 2.457131 | 2.467905 |
| hybrid-chunks | 862 | 0 | 0.000000 | 2.257082 | 3.385623 | 3.540626 |
| lodestone-lexical | 0 | 0 | 0.000000 | 10.402419 | 12.539161 | 12.825675 |
| lodestone-hybrid | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| lodestone-rerank | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| agentic-ask | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| grep-agent | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| full-context | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

## Leakage
- dropped: 0
- histogram: none

## Caveats
- hash embedder is not semantic
- lodestone-hybrid skipped: not implemented in this change
- lodestone-rerank skipped: not implemented in this change
- agentic-ask skipped: not implemented in this change
- grep-agent skipped: not implemented in this change
- full-context skipped: not implemented in this change
- leakage stats are a placeholder until real-corpus question generation

## Failures
- none
```
