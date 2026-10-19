# Threads connector, whole-thread upsert and bursts

Feature base: `main` at `12713b42d5c6db83f6fd76fb3d24fee8a264bdb0`.
Branch: `feat/threads-bursts`.
OpenSpec change: `add-threads-and-bursts`.
Existing migrations were not edited. Schema version remains 3.

## OpenSpec

```text
$ openspec --version
1.14.3

$ openspec validate add-threads-and-bursts --strict
Change 'add-threads-and-bursts' is valid

$ openspec validate --all --strict
✓ change/add-threads-and-bursts
✓ spec/chunkers-sources
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 6 passed, 0 failed (6 items)
```

```text
$ openspec list
Changes:
  add-threads-and-bursts     ✓ Complete
```

Archive after merge as a direct commit on main.

## Requirement checklist

- [x] FR-011: `test_fr_011_malformed_jsonl_reports_line_numbers`, `test_fr_011_timezone_offsets_z_and_naive_rejected`, `test_fr_011_invalid_thread_objects_skipped`, `test_fr_011_oversize_and_invalid_utf8_lines_skipped`, `test_fr_011_threads_path_must_be_file`, `test_fr_011_default_title_and_source_channel`, `test_fr_011_valid_lines_ingested_and_empty_file`, `test_fr_011_slack_export_example_converts_fixture`, `test_fr_011_example_script_rejects_missing_directory`, `test_fr_011_fr_012_threads_sync_search_smoke`.
- [x] FR-012: `test_fr_012_thread_append_updates_in_place_and_removes_old_bursts`, `test_fr_012_changed_thread_replace_is_atomic`, `test_fr_011_fr_012_threads_sync_search_smoke`.
- [x] FR-013: `test_fr_013_cerebras_five_message_figure`, `test_fr_013_burst_records_searchable_via_existing_lanes`.
- [x] FR-020 applied to threads: `test_fr_020_thread_cards_via_fake_llm`.
- [x] FR-021 applied to threads: `test_fr_021_thread_heuristic_resolution_from_last_message`.

## Tests and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
........................................................................ [ 55%]
.........................................................                [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/lodestone/__init__.py                  1      0   100%
src/lodestone/chunking/__init__.py        34      1    97%   30
src/lodestone/chunking/code.py            92      2    98%   95, 108
src/lodestone/chunking/markdown.py        53      0   100%
src/lodestone/cli.py                     169     22    87%   78, 95, 122-123, 136-138, 155-157, 184-185, 191-196, 222-223, 236-238
src/lodestone/config.py                  188      0   100%
src/lodestone/config_io.py                36      3    92%   18, 20, 35
src/lodestone/connectors/__init__.py       3      0   100%
src/lodestone/connectors/files.py        140      6    96%   86, 102, 153-154, 162-163
src/lodestone/connectors/threads.py      102      0   100%
src/lodestone/distill/__init__.py          5      0   100%
src/lodestone/distill/apply.py           113     10    91%   51, 66, 151-152, 158-161, 163, 206
src/lodestone/distill/heuristic.py        63      7    89%   35-36, 42-45, 62
src/lodestone/distill/llm.py              27      1    96%   42
src/lodestone/distill/render.py           45      1    98%   67
src/lodestone/distill/schema.py           15      0   100%
src/lodestone/ingest/__init__.py           0      0   100%
src/lodestone/ingest/bursts.py            38      0   100%
src/lodestone/ingest/pipeline.py         153      4    97%   58, 244-245, 248
src/lodestone/lanes/__init__.py            0      0   100%
src/lodestone/lanes/fts.py                65      0   100%
src/lodestone/providers/__init__.py       21      0   100%
src/lodestone/providers/chat.py          107      5    95%   113, 131, 146, 150, 174
src/lodestone/providers/fake.py           69      6    91%   63-67, 74
src/lodestone/storage/__init__.py          0      0   100%
src/lodestone/storage/costs.py            23      0   100%
src/lodestone/storage/db.py               58      1    98%   31
src/lodestone/storage/records.py          20      2    90%   22-23
src/lodestone/storage/registry.py         28      2    93%   32, 47
src/lodestone/storage/terms.py            17      0   100%
src/lodestone/tokenize.py                 10      0   100%
src/lodestone/workspace.py                83      3    96%   26-27, 77
--------------------------------------------------------------------
TOTAL                                   1778     76    96%
Required test coverage of 80% reached. Total coverage: 95.73%
129 passed in 9.16s
```

```text
$ ruff check .
All checks passed!

$ ruff format --check .
109 files already formatted

$ mypy --strict src
Success: no issues found in 32 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 61 Python files <= 500 lines, all SPDX headers present
```

## Authorship

Recorded after the feature commits on `feat/threads-bursts`:

```text
$ git log 12713b4..HEAD --format='%h %an <%ae> | %cn <%ce>'
6475886 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
5e3bbe6 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
85be147 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
c2d5fe5 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
3274cd8 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log 12713b4..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Slack export, sync, burst search and in-place replace

Temporary workspace `/tmp/lodestone-threads-demo`.

```text
$ lodestone init
Initialised lodestone.toml and database schema 3

$ python3 examples/slack_export_to_jsonl.py tests/fixtures/slack_export --out support.jsonl

$ cat support.jsonl
{"thread_id": "1719830040.000100", "channel": "ckpt-support", "title": "Restore stalls after manifest load. Is NFS stalled?", "messages": [{"id": "m1", "author": "maya", "ts": "2024-07-01T10:34:00Z", "text": "Restore stalls after manifest load. Is NFS stalled?", "reactions": 0}, {"id": "m2", "author": "owen", "ts": "2024-07-01T10:35:00Z", "text": "Setting CKPT_PREFETCH=4 makes it complete. The default is too high for the NFS mount.", "reactions": 2}]}

$ lodestone source add support --kind threads --path support.jsonl
Added source: support

$ lodestone sync --provider fake
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 1, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 1, "cards_llm": 1, "cards_heuristic": 0}

$ lodestone search CKPT_PREFETCH --kind burst --json
{"lane": "fts_raw", "hits": [{"id": 2, "ext_id": "1719830040.000100#burst:1", "source": "support", "kind": "burst", "title": "Restore stalls after manifest load. Is NFS stalled?", "uri": "jsonl://support#1719830040.000100", "snippet": "[2024-07-01T10:35Z] owen: Setting [CKPT_PREFETCH]=4 makes it complete. The default is too high for the NFS mount.", "score": 1.076923076923077e-06, "lane": "fts_raw", "updated_at": "2024-07-01T10:35:00+00:00"}]}

$ lodestone search CKPT_PREFETCH --kind thread
1. support/1719830040.000100 [thread] (fts_raw, 0.000001)
   [2024-07-01T10:34Z] maya: Restore stalls after manifest load. Is NFS stalled?
[2024-07-01T10:35Z] owen: Setting [CKPT_PREFETCH]=4 makes it complete. The default is too high for the NFS mount.

$ lodestone sync --provider fake
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 1, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 1, "cards_llm": 1, "cards_heuristic": 0}

$ lodestone search APPENDED_THREAD_TOKEN --kind thread --json
{"lane": "fts_raw", "hits": [{"id": 1, "ext_id": "1719830040.000100", "source": "support", "kind": "thread", "title": "Restore stalls after manifest load. Is NFS stalled?", "uri": "jsonl://support#1719830040.000100", "snippet": " \u2026 stalls after manifest load. Is NFS stalled?\n[2024-07-01T10:35Z] owen: Setting CKPT_PREFETCH=4 makes it complete. The default is too high for the NFS mount.\n[2026-07-01T12:00Z] maya: [APPENDED_THREAD_TOKEN] confirming the replace.", "score": 9.048178613396005e-07, "lane": "fts_raw", "updated_at": "2026-07-01T12:00:00+00:00"}]}
```

After appending a message, the thread `id` stayed `1`, `updated_at` moved to the new message timestamp, and `APPENDED_THREAD_TOKEN` is searchable on the same `ext_id`.

## CI

PR head `6475886d486d87c2c4e8221ebe94151cdc3de6f3`. All nine jobs `completed` / `success`.

```text
https://github.com/drkwv34/lodestone-kb/actions/runs/39289118808
conclusion: success
```

```json
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39289118808",
  "head_sha": "6475886d486d87c2c4e8221ebe94151cdc3de6f3",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {"name": "build", "status": "completed", "conclusion": "success"},
    {"name": "openspec", "status": "completed", "conclusion": "success"},
    {"name": "licenses", "status": "completed", "conclusion": "success"},
    {"name": "lint-type", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.13)", "status": "completed", "conclusion": "success"},
    {"name": "test (macos-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.11)", "status": "completed", "conclusion": "success"},
    {"name": "test (windows-latest, 3.12, true)", "status": "completed", "conclusion": "success"}
  ]
}
```

Do not merge in this run. Archive after merge as a direct commit on main.
