# Workspace foundation evidence

Implements the workspace foundation only: configuration, workspace setup, schema v1, local diagnostic
probes and blocking repository gates. Five supplied specifications were committed
first in 272b0e3. No paid APIs. Implementation branch and OpenSpec change used the
historical slug recorded in the command transcripts below.

PR #1 was merged locally on main as Christian after CI succeeded on dbdea77.
The merge, direct archive commit and evidence were pushed. OpenSpec is archived
and strictly validated; an annotated tag is published on the merge commit. The gh CLI API remains Forbidden; the user independently
verified CI and explicitly authorised completion on 2026-10-17. Git push and the
GitHub connector work. Historical CLI failures below are retained as evidence.

## E1 — real OpenSpec CLI

```text
$ npm i -g @fission-ai/openspec@latest; openspec --version
1.14.3
```
Installed globally under a writable workspace prefix. `openspec init --tools none`
and `openspec new change` created the real project/change (historical slug in the transcripts below).

```text
$ openspec validate day-1-scaffold --strict
Change 'day-1-scaffold' is valid
```

```text
$ openspec validate --all --strict
✓ change/day-1-scaffold
Totals: 1 passed, 0 failed (1 items)
```

```text
$ openspec list
Changes:
  day-1-scaffold     13/15 tasks   just now
```

After-archive validation output is pasted in the post-merge section below.

## E2 — remote CI and blocker

Final PR-head CI: https://github.com/drkwv34/lodestone-kb/actions/runs/39058358316
for `dbdea77c2bff55f0659fa0e1122164c0b55352a0`. Actual connector output:

```json
{
  "workflow_runs": [
    {
      "id": 39058358316,
      "name": "ci",
      "status": "completed",
      "conclusion": "success",
      "run_number": 6,
      "jobs_url": "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs/39058358316/jobs",
      "logs_url": "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs/39058358316/logs",
      "workflow_id": 387873939
    }
  ]
}
```

The earlier checkpoint and historical CLI blocker follow.

CI checkpoint: https://github.com/drkwv34/lodestone-kb/actions/runs/39058162855
for head `bd10aff2166e147f64a3af1599f19db2dd7ac956`.
The GitHub connector returned this actual output (not a gh transcript):

```json
{
  "workflow_runs": [
    {
      "id": 39058162855,
      "name": "ci",
      "status": "completed",
      "conclusion": "success",
      "run_number": 4,
      "jobs_url": "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs/39058162855/jobs",
      "logs_url": "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs/39058162855/logs",
      "workflow_id": 387873939
    }
  ]
}
```

All nine job conclusions from the connector:

```json
[
  {
    "name": "build",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "licenses",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "openspec",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "lint-type",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (windows-latest, 3.12, true)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.13)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.11)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.12)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (macos-latest, 3.12)",
    "status": "completed",
    "conclusion": "success"
  }
]
```

The documentation commit containing this evidence triggers a fresh head run;
its final result and complete authorship log are pasted in the PR description.
The specifically required gh conclusion output remains blocked:

```text
$ gh run view 39058162855 --repo drkwv34/lodestone-kb --json conclusion
failed to get run: Get "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs/39058162855?exclude_pull_requests=true": Forbidden
```


```text
$ gh run list --repo drkwv34/lodestone-kb --branch day-1-scaffold --json databaseId,headSha,status,conclusion,url
failed to get runs: Get "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs?per_page=20&exclude_pull_requests=true&branch=day-1-scaffold": Forbidden
```

## E3 — authorship from the first commit

The inherited root commit has a GitHub committer. Rewriting it would violate the
no-history-rewrite instruction; this exception is reported, not marked passed.
All new commits use Christian as both author and committer. Snapshot below is
through the CI checkpoint bd10aff; the PR description also records final HEAD.

```text
$ git log --reverse --format='%h %an <%ae> | %cn <%ce>'
a29d735 Christian Agila <87576768+drkwv34@users.noreply.github.com> | GitHub <noreply@github.com>
272b0e3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
82c9a2e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9fa446c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
91557d9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
bd10aff Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log --format=%B | rg -i -c 'co-authored-by' (print 0 if no matches)
0
```

## E4 — local pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=70
............................                                             [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.14-final-0 _______________

Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src/lodestone/__init__.py               1      0   100%
src/lodestone/cli.py                   59      2    97%   62, 79
src/lodestone/config.py               145      0   100%
src/lodestone/storage/__init__.py       0      0   100%
src/lodestone/storage/db.py            58      1    98%   31
src/lodestone/workspace.py             18      2    89%   18-19
-----------------------------------------------------------------
TOTAL                                 281      5    98%
Required test coverage of 70% reached. Total coverage: 98.22%
28 passed in 1.79s
```

## E5 — requirement checklist and proving tests

| Requirement | Test / gate |
|---|---|
| FR-001 | `test_fr_001_init_idempotence_smoke`, `test_fr_001_init_runtime_error_on_newer_database` |
| FR-002 | `test_fr_002_five_invalid_fixtures` (5 fixtures), `test_fr_002_full_architecture_config_and_relative_paths`, `test_fr_002_example_and_independent_defaults`, `test_fr_002_config_show_smoke`, `test_fr_002_rejects_inline_secrets_without_echoing_values`, `test_fr_002_unreadable_config_and_init_error` |
| FR-082 | `test_fr_082_migration_apply_schema_and_idempotence`, `test_fr_082_newer_version_refused_without_mutation`, `test_fr_082_failed_migration_rolls_back_ddl_and_version`, `test_fr_082_missing_migration_and_active_transaction`, `test_fr_082_forward_upgrade_from_v1_fixture` |
| FR-080 (partial) | `test_fr_080_fts5_identifier_probe`, `test_fr_080_disabled_fts5_reports_remediation`, `test_fr_080_missing_and_outdated_database`, `test_fr_080_doctor_smoke` |
| FR-005 preview | `test_fr_005_secret_redaction_preview` |
| NFR-011 | CI matrix Ubuntu 3.11/3.12/3.13, macOS 3.12, Windows 3.12; E2E tests named `smoke`; all matrix jobs succeeded at bd10aff (E2) |
| NFR-012 initial gates | `test_nfr_012_module_limit_and_spdx_headers`; 70% coverage, mypy strict, Ruff, import-linter and module gates |
| NFR-017 | `test_nfr_017_license_and_notice`; `pip-licenses --partial-match --fail-on='GPL;AGPL'` report generated locally and uploaded by CI |

Local gate outputs:

```text
$ ruff check .
All checks passed!
```

```text
$ ruff format --check .
24 files already formatted
```

```text
$ mypy --strict src
Success: no issues found in 6 source files
```

```text
$ python scripts/check_modules.py
Module gate: 13 Python files <= 500 lines, all SPDX headers present
```

```text
$ lint-imports --config importlinter.ini
CLI above workspace above storage above config KEPT
Contracts: 1 kept, 0 broken.
```

```text
$ pip-licenses --format=markdown --partial-match --fail-on='GPL;AGPL' --output-file=work/licenses.md
created path: work/licenses.md
```

## E6 — installed-wheel CLI transcript

```text
$ lodestone init && lodestone doctor
Initialised lodestone.toml and database schema 1
Python: 3.12.14
SQLite: 3.53.1
FTS5: available (identifier tokenizer probe passed)
Database schema: 1 (supported: 1)
Doctor: OK (local Day 1 probes)
```

```text
$ python -m build --outdir work/dist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - hatchling>=1.32
* Getting build dependencies for sdist...
* Installed build dependency versions:
  - hatchling==1.32.4
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - hatchling>=1.32
* Getting build dependencies for wheel...
* Installed build dependency versions:
  - hatchling==1.32.4
* Building wheel...
Successfully built lodestone_kb-0.1.0.dev0.tar.gz and lodestone_kb-0.1.0.dev0-py3-none-any.whl
```

The wheel was installed into a separate virtual environment, and the CLI smoke
script ran from a temporary directory outside the checkout. Ruff formatting
excludes immutable uploaded spec snapshots; all implementation modules are checked.

## Post-merge archive on main (2026-10-17)

Merge commit: `443fde2271118f00e2111aab3ecaec98ab7eee8e`. PR #1 is closed and merged. No history was rewritten.

```text
$ git show --no-patch --format=fuller 443fde2271118f00e2111aab3ecaec98ab7eee8e
commit 443fde2271118f00e2111aab3ecaec98ab7eee8e
Merge: a29d735 dbdea77
Author:     Christian Agila <87576768+drkwv34@users.noreply.github.com>
AuthorDate: Sat Oct 17 19:23:20 2026 +0000
Commit:     Christian Agila <87576768+drkwv34@users.noreply.github.com>
CommitDate: Sat Oct 17 19:23:20 2026 +0000

    Merge day-1-scaffold: scaffold, config, storage, CLI skeleton, CI (Day 1)
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb.git
   a29d735..443fde2  main -> main
```

```text
$ openspec archive day-1-scaffold --yes
Task status: 13/15 tasks
Warning: 2 incomplete task(s) found. Continuing due to --yes flag.

Specs to update:
  repository-gates: create
  workspace-foundation: create
Applying changes to openspec/specs/repository-gates/spec.md:
  + 3 added
Applying changes to openspec/specs/workspace-foundation/spec.md:
  + 5 added
Totals: + 8, ~ 0, - 0, → 0
Specs updated successfully.
Change 'day-1-scaffold' archived as '2026-10-17-day-1-scaffold'.
```
The two archive warnings concern the delivery tasks themselves; they are completed in the final delivery record after archive/tag publication. No validation check was skipped.

```text
$ openspec validate --all --strict
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 2 passed, 0 failed (2 items)
```

```text
$ openspec list
No active changes found.
```

```text
$ git log --format='%h %an <%ae> | %cn <%ce>' a29d735..HEAD
443fde2 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
dbdea77 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
bd10aff Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
91557d9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9fa446c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
82c9a2e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
272b0e3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ co-authored-by count in git log --format=%B a29d735..HEAD (case-insensitive)
0
```

This authorship snapshot precedes the direct archive commit that stores it. The final PR description and chat include the completed main-branch log.

## Published archive and merge-commit tag


```text
$ git push origin main (archive commit)
To https://github.com/drkwv34/lodestone-kb.git
   443fde2..03432c7  main -> main
```

```text
$ git push origin refs/tags/day-1
To https://github.com/drkwv34/lodestone-kb.git
 * [new tag]         day-1 -> day-1
```

```text
$ git tag -l
day-1
```

```text
$ git rev-parse day-1^{commit}
443fde2271118f00e2111aab3ecaec98ab7eee8e
```

```text
$ openspec validate --all --strict
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 2 passed, 0 failed (2 items)
```

```text
$ git log --format='%h %an <%ae> | %cn <%ce>' a29d735..HEAD
03432c7 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
443fde2 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
dbdea77 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
bd10aff Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
91557d9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9fa446c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
82c9a2e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
272b0e3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ co-authored-by count (case-insensitive, a29d735..HEAD commit messages)
0
```

Snapshot includes the archive commit and precedes this final evidence commit. Both delivery tasks in the archived change are now checked complete. The annotated tag remains on merge 443fde2.
