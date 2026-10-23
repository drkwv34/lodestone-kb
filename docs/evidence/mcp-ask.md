# Read-only MCP server and ask command

Feature base: `main` at `94ea1e9`.
Branch: `feat/mcp-ask`.
OpenSpec change: `add-mcp-server-and-ask`.
Existing migrations were not edited. Schema version remains 3.

Implements FR-052, FR-053, FR-054, FR-055, FR-056, and MCP exposure of FR-043
and FR-044. Coverage gate ramps to 85% (NFR-012). MCP SDK pin is `mcp>=2,<3`
(`MCPServer`); see [decision 0007](../decisions/0007-mcp-sdk-v2.md).

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
1.14.3

$ openspec validate add-mcp-server-and-ask --strict
Change 'add-mcp-server-and-ask' is valid

$ openspec validate --all --strict
✓ change/add-mcp-server-and-ask
✓ spec/chunkers-sources
✓ spec/fusion-search
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 10 passed, 0 failed (10 items)

$ openspec list
Changes:
  add-mcp-server-and-ask     ✓ Complete
```

## Requirement checklist

- [x] FR-052: `test_fr_052_mcp_tools_validate_against_schema`, `test_fr_052_offline_mcp_makes_no_network`, `test_fr_052_readonly_db_rejects_writes`
- [x] FR-043 MCP: `test_fr_043_mcp_who_knows_returns_people`
- [x] FR-044 MCP: `test_fr_044_mcp_recent_returns_evidence`
- [x] FR-053: `test_fr_053_citations_only_retrieved_ids`, `test_fr_053_empty_evidence_refuses`, `test_fr_053_sdk_ask_with_fake_provider`
- [x] FR-054: `test_fr_054_planner_fallback_on_malformed_plan`
- [x] FR-055: `test_fr_055_adversarial_sufficiency_terminates`
- [x] FR-056: `test_fr_056_injection_payloads_do_not_alter_tools`
- [x] FR-051 ask/mcp: `test_fr_051_ask_and_mcp_commands`

## Authorship (feature range)

```text
$ git log 94ea1e9..HEAD --format='%h %an <%ae> | %cn <%ce>'
a887390 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
4072639 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3258631 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
a111189 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
d0b7550 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log 94ea1e9..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
179 passed, 3 deselected in 22.57s
TOTAL                                     3670    270    93%
Required test coverage of 85% reached. Total coverage: 92.64%
```

## CI

PR head `a88739073991cf533c98bebc3f12212449dcfa1d`. Run URL:

https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170

```text
conclusion: success
```

```json
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170",
  "head_sha": "a88739073991cf533c98bebc3f12212449dcfa1d",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {"name": "lint-type", "status": "completed", "conclusion": "success"},
    {"name": "openspec", "status": "completed", "conclusion": "success"},
    {"name": "licenses", "status": "completed", "conclusion": "success"},
    {"name": "build", "status": "completed", "conclusion": "success"},
    {"name": "test (windows-latest, 3.12, true)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.11)", "status": "completed", "conclusion": "success"},
    {"name": "test (macos-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.13)", "status": "completed", "conclusion": "success"}
  ]
}
```

```text
$ gh pr checks 12
build	pass	30s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120525976719
licenses	pass	27s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120525976667
lint-type	pass	32s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120525976469
openspec	pass	8s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120525976652
test (macos-latest, 3.12)	pass	1m25s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120526252895
test (ubuntu-latest, 3.11)	pass	1m3s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120526252892
test (ubuntu-latest, 3.12)	pass	52s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120526252819
test (ubuntu-latest, 3.13)	pass	55s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120526253001
test (windows-latest, 3.12, true)	pass	1m17s	https://github.com/drkwv34/lodestone-kb/actions/runs/39986225170/job/120526252778
```

All nine jobs including macOS succeeded.

## Demo transcript

```text
$ # scripted MCP session on a fixture workspace (in-process Client)
tools: ['get_record', 'grep', 'list_sources', 'recent', 'search', 'who_knows']
call search {'query': 'ERR_MANIFEST_TIMEOUT', 'limit': 2}
{
  "hits": [
    {
      "schema": "evidence.v1",
      "id": 5,
      "source": "wiki",
      "kind": "doc",
      "title": "manifest",
      "snippet": "# Manifest restore\n[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.\nSet CKPT_PREFETCH=4 and retry the manifest load.\n",
      "score": 0.04918032786885246
    }
  ]
}
call get_record {'ext_id': 'manifest.md'}
{
  "record": {"id": 5, "ext_id": "manifest.md", "source": "wiki", "kind": "doc", "title": "manifest"},
  "raw_text": "# Manifest restore\nERR_MANIFEST_TIMEOUT occurs when restoring a checkpoint over NFS.\nSet CKPT_PREFETCH=4 and retry the manifest load.\n",
  "children": [{"id": 6, "kind": "section", "title": "Manifest restore"}]
}
call who_knows {'topic': 'manifest'}
{"people": []}
call recent {'limit': 2}
{"hits": [{"schema": "evidence.v1", "id": 8, "source": "wiki", "kind": "section", "title": "keep"}]}

$ lodestone ask "Why does restore stall?" --provider fake --offline
text: The retrieved records support this answer [E1] [E2] [E3].
citations: ['E1', 'E2', 'E3']
insufficient_evidence: False
rounds: 1
```

## Merge and archive

Merge commit: `a798ece2115eb5138c0d784f6bd4323328eed388`. Author and committer
are Christian Agila <87576768+drkwv34@users.noreply.github.com>. No co-author
trailers.

```text
$ git merge --no-ff feat/mcp-ask -m "Merge pull request #12 from drkwv34/feat/mcp-ask"
Merge made by the 'ort' strategy.
```

```text
$ git log -1 --format='%H%n%h %an <%ae> | %cn <%ce>%n%B'
a798ece2115eb5138c0d784f6bd4323328eed388
a798ece Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
Merge pull request #12 from drkwv34/feat/mcp-ask
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb
   94ea1e9..a798ece  main -> main
```

GitHub recorded the PR as merged:

```text
$ gh pr view 12 --json state,mergedAt,mergeCommit,url,headRefOid
{"headRefOid":"a88739073991cf533c98bebc3f12212449dcfa1d","mergeCommit":{"oid":"a798ece2115eb5138c0d784f6bd4323328eed388"},"mergedAt":"2026-10-23T16:32:25Z","state":"MERGED","url":"https://github.com/drkwv34/lodestone-kb/pull/12"}
```

```text
$ git log 94ea1e9..HEAD --format='%h %an <%ae> | %cn <%ce>'
a798ece Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
a887390 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
4072639 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3258631 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
a111189 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
d0b7550 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log 94ea1e9..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

```text
$ openspec archive add-mcp-server-and-ask --yes
Task status: ✓ Complete

Specs to update:
  mcp-ask: create
  repository-gates: update
Applying changes to openspec/specs/mcp-ask/spec.md:
  + 7 added
Applying changes to openspec/specs/repository-gates/spec.md:
  ~ 1 modified
Totals: + 7, ~ 1, - 0, → 0
Specs updated successfully.
Change 'add-mcp-server-and-ask' archived as '2026-10-23-add-mcp-server-and-ask'.
```

```text
$ openspec validate --all --strict
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
Totals: 10 passed, 0 failed (10 items)
```

```text
$ openspec list
No active changes found.
```

