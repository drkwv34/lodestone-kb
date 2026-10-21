# Fused search with RRF, decay, explain and grep lane

Feature base: `main` at `f05afd8ef6484d36aed0b448cbbc9664834adeb8`.
Branch: `feat/fusion-search`.
OpenSpec change: `add-fusion-search`.
Existing migrations were not edited. Schema version remains 3.

Implements FR-034, FR-035, FR-036, FR-037, FR-038, FR-040, FR-041 (complete),
FR-042, NFR-001, NFR-002, NFR-003 (first measurements). LLM rerank (FR-039) is
out of scope.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.14.3

$ openspec validate add-fusion-search --strict
Change 'add-fusion-search' is valid

$ openspec validate --all --strict
✓ change/add-fusion-search
✓ spec/chunkers-sources
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 8 passed, 0 failed (8 items)

$ openspec list
Changes:
  add-fusion-search     ✓ Complete
```

## Requirement checklist

- [x] FR-034: `test_fr_034_grep_lane_and_regex_guard`, `test_fr_040_fr_034_fused_explain_and_grep_cli`
- [x] FR-035: `test_fr_035_rrf_reproduces_cerebras_figure`
- [x] FR-036: `test_fr_036_decay_orders_threads_and_respects_floor`, `test_fr_036_no_decay_restores_raw_fused_order`
- [x] FR-037: `test_fr_037_collapse_and_per_source_cap`
- [x] FR-038: `test_fr_038_neighbour_expansion_edge_cases`
- [x] FR-040: `test_fr_040_explain_contributions_sum_to_fused_score`, `test_fr_040_fr_034_fused_explain_and_grep_cli`
- [x] FR-041: `test_fr_041_filters_property_500_combinations`, `test_fr_041_metadata_filter_parser`
- [x] FR-042: `test_fr_042_evidence_packet_schema`
- [x] NFR-001: `test_nfr_001_lexical_search_p95`
- [x] NFR-002: `test_nfr_002_heuristic_ingest_throughput`
- [x] NFR-003: `test_nfr_003_incremental_no_change_sync`

## Tests and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
155 passed, 3 deselected in 15.12s
TOTAL 2740 144 95%
Required test coverage of 80% reached. Total coverage: 94.74%
```

Perf tests are deselected from the default run (`pytest -m perf`).

```text
$ ruff check .
All checks passed!

$ ruff format --check .
files already formatted

$ mypy --strict src
Success: no issues found in source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: Python files <= 500 lines, all SPDX headers present
```

Lint, types, import-linter and the module-size gate also passed as CI job
`lint-type` on the PR head (see CI below).

## Perf (`pytest -m perf`, Linux 6.12.94+ x86_64, Python 3.12.3)

```text
NFR-001 p95_ms=2.692 n=20000 machine=Linux 6.12.94+ x86_64 python 3.12.3 samples=50
NFR-002 records_per_s=81.333 processed=20000 elapsed_s=245.904 machine=Linux 6.12.94+ x86_64 python 3.12.3
NFR-003 no_change_sync_s=2.984 processed=0 unchanged=20000 machine=Linux 6.12.94+ x86_64 python 3.12.3
```

NFR-001 target <= 50 ms laptop / 150 ms GitHub runner: met (2.692 ms).
NFR-003 target <= 10 s: met (2.984 s).
NFR-002 target >= 200 records/s: below target at 81.333 records/s. Plan in
`docs/decisions/0006-fusion-perf-baseline.md`.

## Authorship

Recorded on `feat/fusion-search` at PR head `d497683`, then again after the
merge commit on `main`.

```text
$ git log f05afd8..HEAD --format='%h %an <%ae> | %cn <%ce>'
2d07589 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
d497683 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
fb38e41 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
abcea50 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
746cef3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
a31607a Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3014288 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
6b177d2 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
6ed12a3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
7588cb6 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log f05afd8..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Demo

```text
$ lodestone sync --offline
{"processed": 4, "unchanged": 0, "skipped": 5, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 4, "cards_llm": 0, "cards_heuristic": 4}

$ lodestone search "ERR_MANIFEST_TIMEOUT" --explain --offline
1. wiki/manifest.md [doc] (fts_raw, 0.049180)
   explain: fts_raw r=1 c=0.0164 fts_card r=1 c=0.0164 vec_card r=1 c=0.0164 decay=1.0 final=0.04918032786885246
   # Manifest restore
[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.

$ lodestone search "ERR_MANIFEST_TIMEOUT" --lane grep
1. wiki/manifest.md#section:0 [section] (grep, 1.000000)
   1: # Manifest restore
2: ERR_MANIFEST_TIMEOUT occurs when restoring a checkpoint over NFS.

$ lodestone search "(a+)+" --lane grep --regex
Configuration error: pathological regex rejected
exit=2
```

`--explain` shows per-lane rank and RRF contribution; contributions times decay
equal the fused score. The grep lane returns line context. Nested-quantifier
regex `(a+)+` is rejected.

## CI

Final PR head `d497683783197de8ee73f2bd5da77b7afbe1ca10`. All nine jobs
`completed` / `success`.

```text
https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216
conclusion: success
```

```json
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216",
  "head_sha": "d497683783197de8ee73f2bd5da77b7afbe1ca10",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {"name": "build", "status": "completed", "conclusion": "success"},
    {"name": "licenses", "status": "completed", "conclusion": "success"},
    {"name": "lint-type", "status": "completed", "conclusion": "success"},
    {"name": "openspec", "status": "completed", "conclusion": "success"},
    {"name": "test (macos-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.11)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.13)", "status": "completed", "conclusion": "success"},
    {"name": "test (windows-latest, 3.12, true)", "status": "completed", "conclusion": "success"}
  ]
}
```

```text
$ gh pr checks 9
build	pass	26s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353557152
licenses	pass	20s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353557123
lint-type	pass	24s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353557271
openspec	pass	11s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353556795
test (macos-latest, 3.12)	pass	1m34s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353789344
test (ubuntu-latest, 3.11)	pass	52s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353789622
test (ubuntu-latest, 3.12)	pass	57s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353789423
test (ubuntu-latest, 3.13)	pass	39s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353789456
test (windows-latest, 3.12, true)	pass	1m16s	https://github.com/drkwv34/lodestone-kb/actions/runs/39637953216/job/119353789666
```

Earlier head `fb38e41e8d97a02876d284580cacbd584f6de522` failed only the `build`
wheel-smoke job because fused JSON packets emit `evidence.v1` rather than
`ext_id`. `d497683` updated `scripts/smoke_wheel.py`; the rerun succeeded.

## Merge and archive

Merge commit: `2d075899d032652268affcfca111acd61e624ecf`. Author and committer
are Christian Agila <87576768+drkwv34@users.noreply.github.com>. No co-author
trailers.

```text
$ git merge --no-ff feat/fusion-search -m "Merge pull request #9 from drkwv34/feat/fusion-search"
Merge made by the 'ort' strategy.
```

```text
$ git rev-parse HEAD
2d075899d032652268affcfca111acd61e624ecf
```

```text
$ git log -1 --format='%H%n%h %an <%ae> | %cn <%ce>%n%B'
2d075899d032652268affcfca111acd61e624ecf
2d07589 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
Merge pull request #9 from drkwv34/feat/fusion-search
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb
   f05afd8..2d07589  main -> main
```

GitHub recorded the PR as merged:

```text
$ gh pr view 9 --json state,mergedAt,mergeCommit,url,headRefOid
{"headRefOid":"d497683783197de8ee73f2bd5da77b7afbe1ca10","mergeCommit":{"oid":"2d075899d032652268affcfca111acd61e624ecf"},"mergedAt":"2026-10-21T16:52:29Z","state":"MERGED","url":"https://github.com/drkwv34/lodestone-kb/pull/9"}
```

```text
$ openspec archive add-fusion-search --yes
Proposal warnings in proposal.md (non-blocking):
  ⚠ Consider splitting changes with more than 10 deltas
Task status: ✓ Complete

Specs to update:
  fusion-search: create
  lexical-search: update
Applying changes to openspec/specs/fusion-search/spec.md:
  + 10 added
Applying changes to openspec/specs/lexical-search/spec.md:
  ~ 1 modified
Totals: + 10, ~ 1, - 0, → 0
Specs updated successfully.
Change 'add-fusion-search' archived as '2026-10-21-add-fusion-search'.
```

```text
$ openspec validate --all --strict
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 8 passed, 0 failed (8 items)
```

```text
$ openspec list
No active changes found.
```
