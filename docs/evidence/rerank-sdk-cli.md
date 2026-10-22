# Rerank, typed SDK facade and CLI polish

Feature base: `main` at `e86ec73f65bd69b5af1f8f576b72bc16d89502b4`.
Branch: `feat/rerank-sdk-cli`.
OpenSpec change: `add-rerank-sdk-cli`.
Existing migrations were not edited. Schema version remains 3. `query_log`
already exists in `0001_init.sql`.

Implements FR-039, FR-043, FR-044, FR-050, FR-051 (non-bench, non-MCP, non-ask),
FR-064, FR-081.

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.14.3

$ openspec validate add-rerank-sdk-cli --strict
Change 'add-rerank-sdk-cli' is valid

$ openspec validate --all --strict
✓ change/add-rerank-sdk-cli
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 9 passed, 0 failed (9 items)

$ openspec list
Changes:
  add-rerank-sdk-cli     ✓ Complete
```

## Requirement checklist

- [x] FR-039: `test_fr_039_rerank_permutes_candidate_pool`, `test_fr_039_rerank_fallback_keeps_fused_order`, `test_fr_039_explain_includes_rerank_score`
- [x] FR-043: `test_fr_043_who_knows_returns_expected_top_expert`
- [x] FR-044: `test_fr_044_recent_deterministic_order`
- [x] FR-050: `test_fr_050_sdk_mypy_strict`, `test_fr_050_readme_doctest`, `test_fr_050_open_directory_and_stats`
- [x] FR-051: `test_fr_051_cli_help_snapshots`, `test_fr_051_search_grep_get_who_knows_recent_stats`
- [x] FR-064: `test_fr_064_provider_preset_snippets_validate`
- [x] FR-081: `test_fr_081_default_query_log_stores_no_text`

## Authorship (feature range)

```text
$ git log e86ec73..HEAD --format='%h %an <%ae> | %cn <%ce>'
34ebb85 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f47ad54 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
6794c86 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
1196b1c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
756b4e8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
fc40039 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
e915765 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log e86ec73..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
167 passed, 3 deselected in 19.20s
TOTAL                                     3177    197    94%
Required test coverage of 80% reached. Total coverage: 93.80%
```

## Demo transcript

```text
$ lodestone init
Initialised lodestone.toml and database schema 3

$ lodestone source add wiki --kind files --path tests/fixtures/corpus --exclude 'drafts/**'
Added source: wiki

$ lodestone source add support --kind threads --path support.jsonl
Added source: support

$ lodestone sync --offline
Skipping binary.txt: binary
Skipping ignored.txt: ignored
Skipping unsupported.csv: unsupported extension
Skipping drafts/draft.md: ignored
Skipping nested/hidden.txt: ignored
{"processed": 5, "unchanged": 0, "skipped": 5, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 5, "cards_llm": 0, "cards_heuristic": 5}

$ lodestone search "ERR_MANIFEST_TIMEOUT" --offline
1. wiki/manifest.md [doc] (fts_raw, 0.049180)
   # Manifest restore
[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.
Set CKPT_PREFETCH=4 and retry the manifest load.

$ lodestone search "ERR_MANIFEST_TIMEOUT" --rerank --offline
notice: rerank skipped: no reranker configured
1. wiki/manifest.md [doc] (fts_raw, 0.049180)
   # Manifest restore
[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.
Set CKPT_PREFETCH=4 and retry the manifest load.

$ lodestone grep "CKPT_PREFETCH"
10 jsonl://support#1719830040.000100:1: [2024-07-01T10:35Z] owen: Setting CKPT_PREFETCH=4 makes it complete. The default is too high for the NFS mount.

$ lodestone who-knows "checkpoint restore" --json
{"people": [{"author": "owen", "score": 0.4, "records": [9]}, {"author": "maya", "score": 0.4, "records": [9]}]}

$ lodestone recent --limit 3
1. wiki/nested/keep.txt#section:0 [section] 2026-10-21T21:53:09.704771+00:00
2. wiki/nested/keep.txt [doc] 2026-10-21T21:53:09.704771+00:00
3. wiki/manifest.md#section:0 [section] 2026-10-21T21:53:09.700768+00:00

$ lodestone stats
{
  "records": 10,
  "sources": 2,
  "schema_version": 3,
  "query_log": 5,
  "store_queries": false
}

$ python3 - <<'PY'
from pathlib import Path
from lodestone import Lodestone
with Lodestone.open(Path('.'), offline=True) as kb:
    print(kb.search('CKPT_PREFETCH').hits[0].title)
    print([(p.author, round(p.score, 4)) for p in kb.who_knows('checkpoint restore')])
PY
manifest
[('owen', 0.4), ('maya', 0.4)]

$ python3 - <<'PY'
import sqlite3
con = sqlite3.connect('.lodestone/index.db')
for qhash, lanes, results, text in con.execute('SELECT qhash, lanes, results, query_text FROM query_log'):
    print({'qhash': qhash[:12]+'…', 'lanes': lanes, 'results': results, 'query_text': text})
con.close()
PY
{'qhash': '2ad1a975a237…', 'lanes': 'fused', 'results': 4, 'query_text': None}
{'qhash': '2ad1a975a237…', 'lanes': 'fused', 'results': 4, 'query_text': None}
{'qhash': 'd204993d9d8e…', 'lanes': 'grep', 'results': 4, 'query_text': None}
{'qhash': '7e66c6314f4f…', 'lanes': 'who_knows', 'results': 2, 'query_text': None}
{'qhash': 'e3b0c44298fc…', 'lanes': 'recent', 'results': 3, 'query_text': None}
{'qhash': 'd204993d9d8e…', 'lanes': 'fused', 'results': 4, 'query_text': None}
```

Default `log.store_queries=false` stores a query hash and null `query_text`.
Offline `--rerank` without a chat provider keeps fused order and adds a notice.

## CI

Final implementation PR head `34ebb85fc12b013b977b408c3b827e00d1796157`.
All nine jobs `completed` / `success`, including `test (macos-latest, 3.12)`.

```text
https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588
conclusion: success
```

```json
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588",
  "head_sha": "34ebb85fc12b013b977b408c3b827e00d1796157",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {"name": "licenses", "status": "completed", "conclusion": "success"},
    {"name": "openspec", "status": "completed", "conclusion": "success"},
    {"name": "build", "status": "completed", "conclusion": "success"},
    {"name": "lint-type", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.11)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.13)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (macos-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (windows-latest, 3.12, true)", "status": "completed", "conclusion": "success"}
  ]
}
```

```text
$ gh pr checks 11
build	pass	24s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950524046
licenses	pass	25s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950523510
lint-type	pass	30s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950524050
openspec	pass	10s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950523894
test (macos-latest, 3.12)	pass	1m21s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950780135
test (ubuntu-latest, 3.11)	pass	1m12s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950779996
test (ubuntu-latest, 3.12)	pass	1m5s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950780108
test (ubuntu-latest, 3.13)	pass	1m9s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950780009
test (windows-latest, 3.12, true)	pass	1m10s	https://github.com/drkwv34/lodestone-kb/actions/runs/39814841588/job/119950780201
```

Python 3.13 first failed on `test_fr_051_cli_help_snapshots` when Rich emitted
ANSI under `FORCE_COLOR`. `34ebb85` compares unstyled help.

Final PR head `710f497de4844d911edee7b62e873da747db497a` (docs-only evidence
commit) was also `success`, all nine jobs including macOS:

```text
https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696
conclusion: success
```

```text
$ gh pr checks 11
build	pass	24s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956728757
licenses	pass	26s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956728688
lint-type	pass	28s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956728857
openspec	pass	9s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956729113
test (macos-latest, 3.12)	pass	1m57s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956993904
test (ubuntu-latest, 3.11)	pass	1m2s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956993195
test (ubuntu-latest, 3.12)	pass	1m3s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956993208
test (ubuntu-latest, 3.13)	pass	1m0s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956993273
test (windows-latest, 3.12, true)	pass	1m18s	https://github.com/drkwv34/lodestone-kb/actions/runs/39816636696/job/119956993456
```

## Merge and archive

Merge commit: `deedf9b0c8b3ce364132794d90eed9f8faf90b58`. Author and committer
are Christian Agila <87576768+drkwv34@users.noreply.github.com>. No co-author
trailers.

```text
$ git merge --no-ff feat/rerank-sdk-cli -m "Merge pull request #11 from drkwv34/feat/rerank-sdk-cli"
Merge made by the 'ort' strategy.
```

```text
$ git log -1 --format='%H%n%h %an <%ae> | %cn <%ce>%n%B'
deedf9b0c8b3ce364132794d90eed9f8faf90b58
deedf9b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
Merge pull request #11 from drkwv34/feat/rerank-sdk-cli
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb
   e86ec73..deedf9b  main -> main
```

GitHub recorded the PR as merged:

```text
$ gh pr view 11 --json state,mergedAt,mergeCommit,url,headRefOid
{"headRefOid":"710f497de4844d911edee7b62e873da747db497a","mergeCommit":{"oid":"deedf9b0c8b3ce364132794d90eed9f8faf90b58"},"mergedAt":"2026-10-22T16:50:58Z","state":"MERGED","url":"https://github.com/drkwv34/lodestone-kb/pull/11"}
```

```text
$ openspec archive add-rerank-sdk-cli --yes
Task status: ✓ Complete

Specs to update:
  fusion-search: update
  rerank-sdk-cli: create
Applying changes to openspec/specs/fusion-search/spec.md:
  + 1 added
Applying changes to openspec/specs/rerank-sdk-cli/spec.md:
  + 7 added
Totals: + 8, ~ 0, - 0, → 0
Specs updated successfully.
Change 'add-rerank-sdk-cli' archived as '2026-10-22-add-rerank-sdk-cli'.
```

```text
$ openspec validate --all --strict
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 9 passed, 0 failed (9 items)
```

```text
$ openspec list
No active changes found.
```
