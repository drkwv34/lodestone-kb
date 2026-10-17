# Markdown/code chunking and source management evidence

Feature base: `main` at `0a949d299d7ca0034b00678f0e205a4894c75b05`.

## OpenSpec

```text
$ openspec --version
1.14.3
```

```text
$ openspec validate add-chunkers-and-sources --strict
Change 'add-chunkers-and-sources' is valid
```

```text
$ openspec list
No active changes found.
```

Archived as `2026-10-17-add-chunkers-and-sources` after merge.
The new capability Purpose describes structural chunking, synchronization and source boundaries.

## Requirement checklist

- [x] FR-015: `test_fr_015_heading_path_golden`, `test_fr_015_fence_atomicity_limits_and_paragraph_target`, `test_fr_015_lossless_bounded_text_property`.
- [x] FR-016: `test_fr_016_class_method_if_for_golden`, `test_fr_016_fr_010_language_goldens`, `test_fr_016_comments_strings_and_fallback`.
- [x] FR-014: `test_fr_014_resync_zero_writes_and_single_file_edit`, `test_fr_014_edit_counts_chunking_and_replaces_children_atomically`, `test_fr_014_tombstone_restore_prune_and_unavailable_root`, `test_fr_014_incomplete_scan_preserves_missing_records`.
- [x] FR-003: `test_fr_003_project_scope_property_200_queries` (200 generated queries), `test_fr_003_project_registry_validation`, `test_fr_003_fr_004_cli_scope_and_errors`.
- [x] FR-004: `test_fr_004_fr_003_fr_005_source_lifecycle_smoke`, `test_fr_004_failed_registry_update_preserves_index`, `test_fr_004_toml_source_removal_reconciles_registry`, `test_fr_004_register_thread_source_without_ingesting`.
- [x] FR-005: `test_fr_005_runtime_secret_overrides_redaction_and_no_persistence`, `test_fr_004_fr_003_fr_005_source_lifecycle_smoke`.
- [x] FR-010 code kinds: `test_fr_010_code_kinds_keep_file_safety_rules`, `test_fr_010_fr_016_code_parent_outline_and_children`, `test_fr_016_fr_010_language_goldens`.

## Test and quality output

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=70
........................................................................ [ 86%]
...........                                                              [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.14-final-0 _______________

Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/lodestone/__init__.py                  1      0   100%
src/lodestone/chunking/__init__.py        34      1    97%   30
src/lodestone/chunking/code.py            92      2    98%   95, 108
src/lodestone/chunking/markdown.py        53      0   100%
src/lodestone/cli.py                     140     14    90%   75, 92, 133-134, 140-145, 171-172, 185-187
src/lodestone/config.py                  187      0   100%
src/lodestone/config_io.py                36      3    92%   18, 20, 35
src/lodestone/connectors/__init__.py       0      0   100%
src/lodestone/connectors/files.py        132      6    95%   76, 92, 143-144, 152-153
src/lodestone/ingest/__init__.py           0      0   100%
src/lodestone/ingest/pipeline.py          86      0   100%
src/lodestone/lanes/__init__.py            0      0   100%
src/lodestone/lanes/fts.py                60      0   100%
src/lodestone/storage/__init__.py          0      0   100%
src/lodestone/storage/db.py               58      1    98%   31
src/lodestone/storage/registry.py         28      2    93%   32, 47
src/lodestone/storage/terms.py            17      0   100%
src/lodestone/tokenize.py                 10      0   100%
src/lodestone/workspace.py                61      2    97%   23-24
--------------------------------------------------------------------
TOTAL                                    995     31    97%
Required test coverage of 70% reached. Total coverage: 96.88%
83 passed in 5.60s
```

```text
$ ruff check .
All checks passed!
```

```text
$ ruff format --check .
63 files already formatted
```

```text
$ mypy --strict src
Success: no issues found in 19 source files
```

```text
$ python scripts/check_modules.py
Module gate: 35 Python files <= 500 lines, all SPDX headers present
```

```text
$ lint-imports --config importlinter.ini

Analyzed 19 files, 26 dependencies.
-----------------------------------

CLI above workspace above storage above config KEPT
Lexical orchestration above connectors and storage KEPT

Contracts: 2 kept, 0 broken.
```

```text
$ python -m build
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

```text
$ python scripts/smoke_wheel.py
Wheel smoke: init, doctor, config, sync, search passed
```

```text
$ pip-licenses --format=markdown --partial-match --fail-on='GPL;AGPL' --output-file=work/licenses.md
created path: work/licenses.md
```

## Source sync demo

Working directory: a fresh local workspace containing `corpus/guide.md` and `corpus/notes.txt`.

```text
$ lodestone init
Initialised lodestone.toml and database schema 2
$ lodestone source add wiki --kind files --path corpus
Added source: wiki
$ lodestone sync
{"processed": 2, "unchanged": 0, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0}
$ python -c 'from pathlib import Path; Path('"'"'corpus/guide.md'"'"').write_text('"'"'# Guide\n## Install\nInstall the updated package.\n'"'"')'
$ lodestone sync
{"processed": 1, "unchanged": 1, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0}
$ lodestone sync
{"processed": 0, "unchanged": 2, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0}
```

## Authorship snapshot

Main snapshot through merge `efa152e049a01482f1196076b560fbe562195bb1`; the archive commit follows this snapshot.

```text
$ git log --format='%h %an <%ae> | %cn <%ce>' 0a949d2..HEAD
efa152e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
0503198 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
58c11a1 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
ca52caa Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
239c9bb Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
391bf5a Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
744890b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
63d1abc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log 0a949d2..HEAD --format=%B | grep -ci 'co-authored-by'
0
```

The range begins at the feature base commit; earlier history is retained.

## CI

PR: https://github.com/drkwv34/lodestone-kb/pull/3

```text
GitHub Actions API output (selected fields):
id: 39070547915
head_sha: 0503198f36db2208b685c4a2c8cef09a2cecf0e0
html_url: https://github.com/drkwv34/lodestone-kb/actions/runs/39070547915
status: completed
conclusion: success

[
  {
    "name": "lint-type",
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
    "name": "build",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (macos-latest, 3.12)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (windows-latest, 3.12, true)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.11)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.13)",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "test (ubuntu-latest, 3.12)",
    "status": "completed",
    "conclusion": "success"
  }
]
```

## Merge and archive

Merge commit: `efa152e049a01482f1196076b560fbe562195bb1`. Both author and committer are Christian Agila
<87576768+drkwv34@users.noreply.github.com>.

```text
$ git merge --no-ff feat/chunkers-sources -m 'Merge feat/chunkers-sources: structural chunkers, incremental sync, source management'
Merge made by the 'ort' strategy.
 README.md                                          |  92 +++++---
 docs/PROGRESS.md                                   |   4 +-
 docs/decisions/0003-chunkers-and-sources.md        |  42 ++++
 docs/evidence/chunkers-sources.md                  | 237 +++++++++++++++++++++
 importlinter.ini                                   |   3 +-
 lodestone.example.toml                             |   2 +-
 .../add-chunkers-and-sources/.openspec.yaml        |   2 +
 .../changes/add-chunkers-and-sources/proposal.md   |  22 ++
 .../specs/chunkers-sources/spec.md                 |  43 ++++
 openspec/changes/add-chunkers-and-sources/tasks.md |  16 ++
 scripts/smoke_wheel.py                             |   7 +-
 src/lodestone/chunking/__init__.py                 |  43 ++++
 src/lodestone/chunking/code.py                     | 155 ++++++++++++++
 src/lodestone/chunking/markdown.py                 |  71 ++++++
 src/lodestone/cli.py                               | 121 ++++++++++-
 src/lodestone/config.py                            |  66 +++++-
 src/lodestone/config_io.py                         |  64 ++++++
 src/lodestone/connectors/files.py                  |  12 +-
 src/lodestone/ingest/pipeline.py                   | 153 ++++++++++---
 src/lodestone/storage/registry.py                  |  57 +++++
 src/lodestone/workspace.py                         |  50 ++++-
 tests/e2e/test_lexical_cli.py                      |  20 +-
 tests/e2e/test_sources.py                          | 230 ++++++++++++++++++++
 tests/fixtures/chunking/figure.code                |  14 ++
 tests/fixtures/chunking/figure.json                |   7 +
 tests/fixtures/chunking/headings.json              |   9 +
 tests/fixtures/chunking/headings.md                |  26 +++
 tests/integration/test_ingest.py                   | 161 +++++++++++++-
 tests/integration/test_projects.py                 |  89 ++++++++
 tests/unit/test_chunkers.py                        | 141 ++++++++++++
 tests/unit/test_config.py                          |  47 ++++
 tests/unit/test_files.py                           |  21 +-
 32 files changed, 1925 insertions(+), 102 deletions(-)
 create mode 100644 docs/decisions/0003-chunkers-and-sources.md
 create mode 100644 docs/evidence/chunkers-sources.md
 create mode 100644 openspec/changes/add-chunkers-and-sources/.openspec.yaml
 create mode 100644 openspec/changes/add-chunkers-and-sources/proposal.md
 create mode 100644 openspec/changes/add-chunkers-and-sources/specs/chunkers-sources/spec.md
 create mode 100644 openspec/changes/add-chunkers-and-sources/tasks.md
 create mode 100644 src/lodestone/chunking/__init__.py
 create mode 100644 src/lodestone/chunking/code.py
 create mode 100644 src/lodestone/chunking/markdown.py
 create mode 100644 src/lodestone/config_io.py
 create mode 100644 src/lodestone/storage/registry.py
 create mode 100644 tests/e2e/test_sources.py
 create mode 100644 tests/fixtures/chunking/figure.code
 create mode 100644 tests/fixtures/chunking/figure.json
 create mode 100644 tests/fixtures/chunking/headings.json
 create mode 100644 tests/fixtures/chunking/headings.md
 create mode 100644 tests/integration/test_projects.py
 create mode 100644 tests/unit/test_chunkers.py
```

```text
$ git rev-parse HEAD
efa152e049a01482f1196076b560fbe562195bb1
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb.git
   0a949d2..efa152e  main -> main
```

```text
$ openspec archive add-chunkers-and-sources --yes
Task status: ✓ Complete

Specs to update:
  chunkers-sources: create
Applying changes to openspec/specs/chunkers-sources/spec.md:
  + 6 added
Totals: + 6, ~ 0, - 0, → 0
Specs updated successfully.
Change 'add-chunkers-and-sources' archived as '2026-10-17-add-chunkers-and-sources'.
```

The archive created a placeholder Purpose; the new capability now has a feature-specific Purpose.

```text
$ openspec validate --all --strict
✓ spec/chunkers-sources
✓ spec/lexical-search
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 4 passed, 0 failed (4 items)
```

```text
$ openspec list
No active changes found.
```
