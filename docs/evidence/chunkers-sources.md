# Markdown/code chunking and source management evidence

Base: latest `main` at `0a949d299d7ca0034b00678f0e205a4894c75b05`.

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
Changes:
  add-chunkers-and-sources     ✓ Complete    just now
```

The change remains active until merge; archive is deferred to the requested follow-up.

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

Snapshot through `58c11a1`; the PR description will include the final head range.

```text
$ git log day-2..HEAD --format='%h %an <%ae> | %cn <%ce>'
58c11a1 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
ca52caa Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
239c9bb Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
391bf5a Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
744890b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
63d1abc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
0a949d2 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
38c7d92 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log day-2..HEAD --format=%B | grep -Eic 'co-authored-by|bot'
0
```

The range begins at the existing tag; older history is retained.

## CI

PR: https://github.com/drkwv34/lodestone-kb/pull/3

```text
GitHub Actions API output (selected fields):
id: 39070348557
head_sha: 58c11a198486d221592b01a60b8110548d8a402c
html_url: https://github.com/drkwv34/lodestone-kb/actions/runs/39070348557
status: completed
conclusion: success

[
  {
    "name": "openspec",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "licenses",
    "status": "completed",
    "conclusion": "success"
  },
  {
    "name": "build",
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

This records the verified PR head `58c11a1`. Updating tracked evidence changes
HEAD; final-head CI and the complete authorship range are pasted in the PR
description. Merge and subsequent OpenSpec archive remain deferred.
