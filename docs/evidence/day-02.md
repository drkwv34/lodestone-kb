# Day 2 evidence — lexical search

Scope: FR-010 (md/txt/rst), FR-014 (hash skeleton), FR-030, FR-032
(infrastructure and requested rare lane), FR-041 (source/kind only).
Base: latest main `2aa63e92f3052e91a3eb4e2cba60545671d8ac41`, including
Day 1 archive/evidence commits after the `day-1` merge tag.
Implementation branch and OpenSpec change: `day-2-lexical-search`.
The original implementation run stopped at the green PR head. The owner authorised
merge, archive and tagging in the 2026-10-17 follow-up; completion output follows below.

## E1 — real OpenSpec

```text
$ openspec --version
1.14.3

$ openspec validate day-2-lexical-search --strict
Change 'day-2-lexical-search' is valid

$ openspec list
Changes:
  day-2-lexical-search     ✓ Complete    just now
```

## E2 — GitHub Actions

Implementation-head checkpoint from the authenticated GitHub connector. The gh
CLI is blocked in this environment, so the actual Actions API result and all nine
job conclusions are pasted below. This run tested the then-current PR head
`cc4d23c07c2a6877a2c6c111231b5fce53f843bc`. The subsequent evidence commit's
final-head run is pasted into [PR #2](https://github.com/drkwv34/lodestone-kb/pull/2)
after it completes; that output can be copied during the authorised follow-up's
direct-on-main archive/evidence commit without changing the tested PR head.

```text
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39065569808",
  "head_sha": "cc4d23c07c2a6877a2c6c111231b5fce53f843bc",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {
      "id": 117492389354,
      "name": "lint-type",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492389522,
      "name": "build",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492389671,
      "name": "openspec",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492389729,
      "name": "licenses",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492492056,
      "name": "test (ubuntu-latest, 3.12)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492492058,
      "name": "test (macos-latest, 3.12)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492492062,
      "name": "test (ubuntu-latest, 3.13)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492492071,
      "name": "test (ubuntu-latest, 3.11)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117492492105,
      "name": "test (windows-latest, 3.12, true)",
      "status": "completed",
      "conclusion": "success"
    }
  ]
}
conclusion: success

CI pytest output (Linux / Python 3.12):
2026-10-17T20:10:59.1096525Z ##[group]Run pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=70
2026-10-17T20:10:59.1096874Z [36;1mpytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=70[0m
2026-10-17T20:11:03.3036202Z TOTAL                                    598     23    96%
2026-10-17T20:11:03.3036482Z Required test coverage of 70% reached. Total coverage: 96.15%
2026-10-17T20:11:03.3036752Z 52 passed in 3.65s
```

## E3 — author and committer

Captured at implementation head `cc4d23c`; final-head log is appended in PR #2.
The range intentionally includes main's two post-Day-1 evidence/archive commits.

```text
$ git log day-1..HEAD --format='%h %an <%ae> | %cn <%ce>'
cc4d23c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
81833d8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3b3990b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f51f3f8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9e545dc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
2aa63e9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
03432c7 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log day-1..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## E4 — pytest and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=70
....................................................                     [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.14-final-0 _______________

Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/lodestone/__init__.py                  1      0   100%
src/lodestone/cli.py                      88     10    89%   66, 83, 98, 118-125
src/lodestone/config.py                  146      0   100%
src/lodestone/connectors/__init__.py       0      0   100%
src/lodestone/connectors/files.py        129      6    95%   70, 86, 137-138, 146-147
src/lodestone/ingest/__init__.py           0      0   100%
src/lodestone/ingest/pipeline.py          55      0   100%
src/lodestone/lanes/__init__.py            0      0   100%
src/lodestone/lanes/fts.py                60      0   100%
src/lodestone/storage/__init__.py          0      0   100%
src/lodestone/storage/db.py               58      1    98%   31
src/lodestone/storage/terms.py            17      0   100%
src/lodestone/tokenize.py                 10      0   100%
src/lodestone/workspace.py                34      6    82%   21-22, 50-63
--------------------------------------------------------------------
TOTAL                                    598     23    96%
Required test coverage of 70% reached. Total coverage: 96.15%
52 passed in 3.56s
```

## E5 — requirement checklist with proving tests

- [x] **FR-010**, md/txt/rst only: `test_fr_010_fixture_globs_gitignore_binary_oversize`,
  `test_fr_010_path_traversal`, `test_fr_010_symlink_jail_and_cycles`,
  `test_fr_010_gitignore_parent_and_nested_negation`,
  `test_fr_010_defaults_and_unsupported`,
  `test_fr_010_gitignore_limit_independent_and_fail_closed`.
- [x] **FR-014**, hash skeleton: `test_fr_014_resync_zero_writes_and_single_file_edit`
  (asserts zero total SQLite changes, zero record writes, stable IDs, exactly one
  changed row after edit, and zero LLM calls), `test_fr_014_hash_normalization_and_version`,
  `test_fr_014_invalid_source_does_not_register`.
- [x] **FR-030**: `test_fr_030_unicode_identifier_tokenization`,
  `test_fr_030_sanitiser_fuzz_1000_strings` (exactly 1,000),
  `test_fr_030_exact_token_ranks_first` (ERR_MANIFEST_TIMEOUT #1),
  `test_fr_030_phrases_prefix_or_and_title_weights`.
- [x] **FR-032**, infrastructure and rare lane:
  `test_fr_032_idf_hand_computed_and_distinct_df`,
  `test_fr_032_rare_lane_requires_rare_query_term`,
  `test_fr_032_triggers_edit_tombstone_delete_and_rollback`,
  `test_fr_032_tokenizer_matches_stats`, `test_fr_032_migration_0002_backfills_existing_v1`.
- [x] **FR-041**, source/kind only: `test_fr_041_source_kind_filters_before_limit`
  (98 source/kind/lane combinations, literal SQL-injection-like filter values,
  and filtering before LIMIT), `test_fr_010_fr_030_fr_041_sync_search_smoke`.
- [x] CLI and read-only lifecycle:
  `test_fr_010_fr_030_cli_errors_and_readonly_search`; existing Day 1 tests retained
  and their schema-version assertions advanced without reducing the checks.

## E6 — terminal demo

A temporary workspace points at a copy of `tests/fixtures/corpus`, source `wiki`,
exclude `drafts/**`. Combined stdout/stderr from the actual commands follows.

```text
$ lodestone sync
Skipping binary.txt: binary
Skipping ignored.txt: ignored
Skipping unsupported.csv: unsupported extension (Day 2: md/txt/rst)
Skipping drafts/draft.md: ignored
Skipping nested/hidden.txt: ignored
{"processed": 4, "unchanged": 0, "skipped": 5, "llm_calls": 0}

$ lodestone search ERR_MANIFEST_TIMEOUT
1. wiki/manifest.md [doc] (fts_raw, 0.732831)
   # Manifest restore
[ERR_MANIFEST_TIMEOUT] occurs when restoring a checkpoint over NFS.
Set CKPT_PREFETCH=4 and retry the manifest load.

$ lodestone sync
Skipping binary.txt: binary
Skipping ignored.txt: ignored
Skipping unsupported.csv: unsupported extension (Day 2: md/txt/rst)
Skipping drafts/draft.md: ignored
Skipping nested/hidden.txt: ignored
{"processed": 0, "unchanged": 4, "skipped": 5, "llm_calls": 0}
```

## Additional required gates

```text
$ ruff check .
All checks passed!

$ ruff format --check .
48 files already formatted

$ mypy --strict src
Success: no issues found in 14 source files

$ lint-imports --config importlinter.ini

╔══╗─────────▶╔╗ ╔╗      ╔╗◀───┐
╚╣╠╝◀─────┐  ╔╝╚╗║║────▶╔╝╚╗   │
 ║║   ╔══╦══╦╩╗╔╝║║  ╔╦═╩╗╔╝╔═╦══╗
 ║║╔══╣╔╗║╔╗║╔╣║ ║║ ╔╬╣╔╗║║ ║│║╔═╝
╔╣╠╣║║║╚╝║╚╝║║║╚╗║╚═╝║║║║║╚╗║═╣║
╚══╩╩╩╣╔═╩══╩╝╚═╝╚═══╩╩╝╚╩═╩╩═╩╝
  └──▶║║                    ▲ 
      ╚╝────────────────────┘


---------
Contracts
---------

Analyzed 14 files, 13 dependencies.
-----------------------------------

CLI above workspace above storage above config KEPT
Lexical orchestration above connectors and storage KEPT

Contracts: 2 kept, 0 broken.

$ python scripts/check_modules.py
Module gate: 27 Python files <= 500 lines, all SPDX headers present

$ pip-licenses --format=markdown --partial-match --fail-on=GPL;AGPL --output-file=work/licenses.md
created path: work/licenses.md
```

## Build and installed-wheel verification

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

$ pip install --force-reinstall --no-deps dist/*.whl
WARNING: The directory '/home/agent/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Processing ./dist/lodestone_kb-0.1.0.dev0-py3-none-any.whl
Installing collected packages: lodestone-kb
  Attempting uninstall: lodestone-kb
    Found existing installation: lodestone-kb 0.1.0.dev0
    Uninstalling lodestone-kb-0.1.0.dev0:
      Successfully uninstalled lodestone-kb-0.1.0.dev0
Successfully installed lodestone-kb-0.1.0.dev0

[notice] A new release of pip is available: 25.0.1 -> 26.2.1
[notice] To update, run: pip install --upgrade pip

$ python scripts/smoke_wheel.py
Initialised lodestone.toml and database schema 2
Python: 3.12.14
SQLite: 3.53.1
FTS5: available (identifier tokenizer probe passed)
Database schema: 2 (supported: 2)
Doctor: OK (local Day 1 probes)
{
  "schema_version": 1,
  "workspace": {
    "db_path": "/tmp/tmp9wewtmgy/.lodestone/index.db",
    "default_project": "default"
  },
  "llm": null,
  "embed": {
    "base_url": "http://localhost:11434/v1",
    "api_key_env": "[REDACTED]",
    "provider": "none",
    "model": "nomic-embed-text",
    "dim": 768,
    "source": "card",
    "batch_size": 64
  },
  "chunks": {
    "target_tokens": "[REDACTED]",
    "max_tokens": "[REDACTED]",
    "chars_per_token": "[REDACTED]",
    "contextualize": false
  },
  "cards": {
    "enabled": true,
    "kinds": [
      "thread",
      "doc",
      "code_file"
    ],
    "prompt_version": "card.v1",
    "max_input_chars": 24000
  },
  "bursts": {
    "idf_min": 4.0,
    "min_chars": 200,
    "w_idf": 1.0,
    "w_len": 1.0,
    "w_react": 1.0,
    "threshold": 1.0
  },
  "retrieval": {
    "lanes": [
      "fts_raw",
      "fts_card",
      "fts_rare",
      "vec_card",
      "vec_chunk",
      "grep"
    ],
    "weights": {
      "fts_raw": 1.0,
      "fts_card": 1.0,
      "fts_rare": 0.7,
      "vec_card": 1.0,
      "vec_chunk": 0.7,
      "grep": 0.5
    },
    "rrf_k": 60,
    "candidate_pool": 20,
    "max_per_source": 3,
    "rerank": false,
    "rerank_keep": 10,
    "expand": 1,
    "expand_max_chars": 4000,
    "rare_idf": 4.0,
    "rare_df_ratio": null,
    "decay": {
      "thread": {
        "half_life_days": 120.0,
        "floor": 0.4
      },
      "doc": {
        "half_life_days": 0.0,
        "floor": 0.0
      },
      "code": {
        "half_life_days": 0.0,
        "floor": 0.0
      }
    }
  },
  "ask": {
    "max_rounds": 3,
    "planner_model": "",
    "synth_model": ""
  },
  "log": {
    "store_queries": false,
    "level": "INFO"
  },
  "sources": [],
  "projects": [
    {
      "name": "default",
      "sources": []
    }
  ]
}
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 0}
Wheel smoke: init, doctor, config, sync, search passed
```

## Scope and delivery notes

Migration `0001_init.sql` and supplied specs are unchanged. Migration 0002 rebuilds
legacy rows and adds FTS/statistics triggers. No new runtime dependencies, paid
APIs, providers, chunks, projects, pruning or fusion were introduced. See decision
0002 for normalisation, Unicode/FTS parity, gitignore, and IDF threshold details.

The following completion record supersedes the original active-change snapshot.
The approved final PR-head CI output is copied here without changing that tested
PR head. Archive and evidence are direct commits on main after the merge.

## Approved final PR-head evidence, copied after merge

## Final PR-head verification — E2 / E3 / E4

The evidence commit is now tested on the exact current PR head. Output below is from the authenticated GitHub connector; the gh CLI is blocked. All nine jobs are successful. This verification was captured before the authorised merge.

```text
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39065777458",
  "head_sha": "927fb4a9d2f367b30398744298b997b2c5bdc633",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {
      "id": 117493010477,
      "name": "lint-type",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493010560,
      "name": "openspec",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493010624,
      "name": "licenses",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493010649,
      "name": "build",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493118450,
      "name": "test (macos-latest, 3.12)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493118455,
      "name": "test (ubuntu-latest, 3.11)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493118486,
      "name": "test (windows-latest, 3.12, true)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493118509,
      "name": "test (ubuntu-latest, 3.13)",
      "status": "completed",
      "conclusion": "success"
    },
    {
      "id": 117493118511,
      "name": "test (ubuntu-latest, 3.12)",
      "status": "completed",
      "conclusion": "success"
    }
  ]
}
conclusion: success
```

Final-head CI pytest output (Linux / Python 3.12):

```text
2026-10-17T20:14:14.2476209Z TOTAL                                    598     23    96%
2026-10-17T20:14:14.2476665Z Required test coverage of 70% reached. Total coverage: 96.15%
2026-10-17T20:14:14.2477011Z 52 passed in 6.54s
```

```text
$ git log day-1..HEAD --format='%h %an <%ae> | %cn <%ce>'
927fb4a Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
cc4d23c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
81833d8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3b3990b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f51f3f8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9e545dc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
2aa63e9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
03432c7 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log day-1..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

This final PR-head output was pasted in PR #2 and copied into this post-merge evidence record.


## Post-merge completion — 2026-10-17

The owner independently verified PR #2 at `927fb4a` and explicitly authorised
the merge/archive/tag follow-up. Both merge parents are preserved; no history
was rewritten. GitHub now reports PR #2 closed and merged at `c8f34aedea0b12a38b378e83fa3457db97037a30`.

```text
$ git merge --no-ff day-2-lexical-search -m 'Merge day-2-lexical-search: tokenizer, files connector, FTS lanes (Day 2)'
Merge made by the 'ort' strategy.
 README.md                                          |  41 ++-
 docs/PROGRESS.md                                   |   5 +-
 docs/decisions/0002-day-2-lexical-foundation.md    |  51 +++
 docs/evidence/day-02.md                            | 409 +++++++++++++++++++++
 importlinter.ini                                   |  10 +
 lodestone.example.toml                             |   8 +
 .../changes/day-2-lexical-search/.openspec.yaml    |   2 +
 openspec/changes/day-2-lexical-search/proposal.md  |  21 ++
 .../specs/lexical-search/spec.md                   |  55 +++
 openspec/changes/day-2-lexical-search/tasks.md     |  17 +
 scripts/smoke_wheel.py                             |  18 +-
 src/lodestone/cli.py                               |  54 ++-
 src/lodestone/config.py                            |   1 +
 src/lodestone/connectors/__init__.py               |   2 +
 src/lodestone/connectors/files.py                  | 164 +++++++++
 src/lodestone/ingest/__init__.py                   |   2 +
 src/lodestone/ingest/pipeline.py                   |  99 +++++
 src/lodestone/lanes/__init__.py                    |   2 +
 src/lodestone/lanes/fts.py                         | 112 ++++++
 src/lodestone/storage/db.py                        |   2 +-
 src/lodestone/storage/migrations/0002_lexical.sql  |  52 +++
 src/lodestone/storage/terms.py                     |  36 ++
 src/lodestone/tokenize.py                          |  25 ++
 src/lodestone/workspace.py                         |  45 ++-
 tests/conftest.py                                  |  47 +++
 tests/e2e/test_lexical_cli.py                      |  84 +++++
 tests/e2e/test_workspace.py                        |  12 +-
 tests/fixtures/corpus/.gitignore                   |   2 +
 tests/fixtures/corpus/binary.txt                   | Bin 0 -> 29 bytes
 tests/fixtures/corpus/chatter.txt                  |   2 +
 tests/fixtures/corpus/drafts/draft.md              |   1 +
 tests/fixtures/corpus/guide.rst                    |   3 +
 tests/fixtures/corpus/ignored.txt                  |   1 +
 tests/fixtures/corpus/manifest.md                  |   3 +
 tests/fixtures/corpus/nested/.gitignore            |   2 +
 tests/fixtures/corpus/nested/hidden.txt            |   1 +
 tests/fixtures/corpus/nested/keep.txt              |   1 +
 tests/fixtures/corpus/unsupported.csv              |   1 +
 tests/integration/test_ingest.py                   |  77 ++++
 tests/integration/test_lexical.py                  | 151 ++++++++
 tests/integration/test_migrations.py               |  39 +-
 tests/unit/test_files.py                           | 121 ++++++
 tests/unit/test_tokenize.py                        |  21 ++
 43 files changed, 1780 insertions(+), 22 deletions(-)
 create mode 100644 docs/decisions/0002-day-2-lexical-foundation.md
 create mode 100644 docs/evidence/day-02.md
 create mode 100644 openspec/changes/day-2-lexical-search/.openspec.yaml
 create mode 100644 openspec/changes/day-2-lexical-search/proposal.md
 create mode 100644 openspec/changes/day-2-lexical-search/specs/lexical-search/spec.md
 create mode 100644 openspec/changes/day-2-lexical-search/tasks.md
 create mode 100644 src/lodestone/connectors/__init__.py
 create mode 100644 src/lodestone/connectors/files.py
 create mode 100644 src/lodestone/ingest/__init__.py
 create mode 100644 src/lodestone/ingest/pipeline.py
 create mode 100644 src/lodestone/lanes/__init__.py
 create mode 100644 src/lodestone/lanes/fts.py
 create mode 100644 src/lodestone/storage/migrations/0002_lexical.sql
 create mode 100644 src/lodestone/storage/terms.py
 create mode 100644 src/lodestone/tokenize.py
 create mode 100644 tests/conftest.py
 create mode 100644 tests/e2e/test_lexical_cli.py
 create mode 100644 tests/fixtures/corpus/.gitignore
 create mode 100644 tests/fixtures/corpus/binary.txt
 create mode 100644 tests/fixtures/corpus/chatter.txt
 create mode 100644 tests/fixtures/corpus/drafts/draft.md
 create mode 100644 tests/fixtures/corpus/guide.rst
 create mode 100644 tests/fixtures/corpus/ignored.txt
 create mode 100644 tests/fixtures/corpus/manifest.md
 create mode 100644 tests/fixtures/corpus/nested/.gitignore
 create mode 100644 tests/fixtures/corpus/nested/hidden.txt
 create mode 100644 tests/fixtures/corpus/nested/keep.txt
 create mode 100644 tests/fixtures/corpus/unsupported.csv
 create mode 100644 tests/integration/test_ingest.py
 create mode 100644 tests/integration/test_lexical.py
 create mode 100644 tests/unit/test_files.py
 create mode 100644 tests/unit/test_tokenize.py
```

```text
$ git show --format=fuller --no-patch HEAD
commit c8f34aedea0b12a38b378e83fa3457db97037a30
Merge: 2aa63e9 927fb4a
Author:     Christian Agila <87576768+drkwv34@users.noreply.github.com>
AuthorDate: Sat Oct 17 20:54:44 2026 +0000
Commit:     Christian Agila <87576768+drkwv34@users.noreply.github.com>
CommitDate: Sat Oct 17 20:54:44 2026 +0000

    Merge day-2-lexical-search: tokenizer, files connector, FTS lanes (Day 2)
```

```text
$ git push origin main
To https://github.com/drkwv34/lodestone-kb.git
   2aa63e9..c8f34ae  main -> main
```

```text
$ openspec archive day-2-lexical-search --yes
Task status: ✓ Complete

Specs to update:
  lexical-search: create
Applying changes to openspec/specs/lexical-search/spec.md:
  + 5 added
Totals: + 5, ~ 0, - 0, → 0
Specs updated successfully.
Change 'day-2-lexical-search' archived as '2026-10-17-day-2-lexical-search'.
```

The archive CLI generated a placeholder Purpose for the new main spec. Initial
strict validation rejected that placeholder; it was replaced with the implemented
capability's purpose, without changing any requirements or checks.

```text
$ openspec validate --all --strict
✗ spec/lexical-search
  ⚠ [WARNING] overview: Purpose section is still a placeholder rather than a Purpose anyone wrote (the sentence `openspec archive` writes for a new capability, or a `TBD`/`TODO` marker left in its place). Replace it with what this capability is for, editing the main spec directly: a `## Purpose` in a delta is read only when the capability is created, so it cannot replace this one.
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 2 passed, 1 failed (3 items)
Details: openspec validate lexical-search --type spec
```

```text
$ openspec validate --all --strict
✓ spec/lexical-search
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 3 passed, 0 failed (3 items)
```

```text
$ openspec list
No active changes found.
```

Authorship snapshot on main at the merge commit, before committing the archive
and this evidence update (the final delivery log is also pasted in chat):

```text
$ git log --format='%h %an <%ae> | %cn <%ce>' day-1..HEAD
c8f34ae Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
927fb4a Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
cc4d23c Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
81833d8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3b3990b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f51f3f8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9e545dc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
2aa63e9 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
03432c7 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>

$ git log day-1..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

Archive location: `openspec/changes/archive/2026-10-17-day-2-lexical-search/`.
The `day-2` tag target is the merge commit `c8f34aedea0b12a38b378e83fa3457db97037a30`;
publication is recorded after the tag push succeeds.
