# Day 01 evidence — partial delivery

Implements Day 1 only: configuration, workspace setup, schema v1, local diagnostic
probes and blocking repository gates. Five supplied specifications were committed
first in 272b0e3. No paid APIs. Branch/change: `day-1-scaffold`.

Delivery is partial: the installed gh CLI cannot access GitHub API endpoints in
this environment (`Forbidden`). Git push works; the GitHub connector is used to
open a ready PR. Main, tag and archive are deliberately pending the prescribed
CI/merge workflow. No archive validation is claimed before an archive exists.

## E1 — real OpenSpec CLI

```text
$ npm i -g @fission-ai/openspec@latest; openspec --version
1.14.3
```
Installed globally under a writable workspace prefix. `openspec init --tools none`
and `openspec new change day-1-scaffold` created the real project/change.

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
  day-1-scaffold     11/15 tasks   just now
```

After-archive `openspec validate --all --strict`: PENDING, archive must follow merge.

## E2 — remote CI and blocker

Remote CI run URL/conclusion: pending PR creation and observation. No remote
success is claimed. The required gh output is blocked:

```text
$ gh run list --repo drkwv34/lodestone-kb --branch day-1-scaffold --json databaseId,headSha,status,conclusion,url
failed to get runs: Get "https://api.github.com/repos/drkwv34/lodestone-kb/actions/runs?per_page=20&exclude_pull_requests=true&branch=day-1-scaffold": Forbidden
```

## E3 — authorship from the first commit

The inherited root commit has a GitHub committer. Rewriting it would violate the
no-history-rewrite instruction; this exception is reported, not marked passed.
All new commits use Christian as both author and committer. Snapshot below is
through the implementation commits; the PR description also records final HEAD.

```text
$ git log --reverse --format='%h %an <%ae> | %cn <%ce>'
a29d735 Christian Agila <87576768+drkwv34@users.noreply.github.com> | GitHub <noreply@github.com>
272b0e3 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
82c9a2e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9fa446c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
91557d9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
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
| NFR-011 | CI matrix Ubuntu 3.11/3.12/3.13, macOS 3.12, Windows 3.12; E2E tests named `smoke`; remote result pending |
| NFR-012 Day 1 | `test_nfr_012_module_limit_and_spdx_headers`; 70% coverage, mypy strict, Ruff, import-linter and module gates |
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
