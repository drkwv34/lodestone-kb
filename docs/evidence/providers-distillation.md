# Chat providers, FakeLLM, distillation cards and cost log

Feature base: `main` at `376de6af05e4e382e595d8c41ac496d5ff40575c`.
Branch: `feat/providers-distillation`.
OpenSpec change: `add-providers-and-distillation`.
Schema version 3 (migration `0003_card_fts.sql`); existing migrations were not edited.
Coverage gate raised to 80% in `pyproject.toml` and `.github/workflows/ci.yml`.

## OpenSpec

```text
$ openspec --version
1.14.3

$ openspec validate add-providers-and-distillation --strict
Change 'add-providers-and-distillation' is valid

$ openspec validate --all --strict
✓ change/add-providers-and-distillation
✓ spec/chunkers-sources
✓ spec/lexical-search
✓ spec/repository-gates
✓ spec/workspace-foundation
Totals: 5 passed, 0 failed (5 items)
```

Archive after merge as a direct commit on main.

## Requirement checklist

- [x] FR-020: `test_fr_020_malformed_json_retry_then_valid`, `test_fr_020_malformed_json_fallback_heuristic`.
- [x] FR-021: `test_fr_021_golden_heuristic_cards`, `test_fr_021_entities_rank_by_idf`.
- [x] FR-022: `test_fr_022_norm_text_and_card_embed_input`, `test_fr_022_embed_source_change_requeues_embeddings_only`, `test_fr_022_head_tail_truncation`.
- [x] FR-023: `test_fr_023_cache_hit_ratio_and_model_change`.
- [x] FR-024: `test_fr_024_provenance_and_get_record`.
- [x] FR-025: `test_fr_025_contextual_prefix_is_fts_matchable`.
- [x] FR-026: `test_fr_026_cost_totals_equal_sum_of_log_rows`, `test_fr_026_fr_063_cost_and_fake_provider_resync`.
- [x] FR-031: `test_fr_031_paraphrase_found_only_by_fts_card`.
- [x] FR-060: `test_fr_060_provider_fault_injection`, `test_fr_060_non_retryable_client_error`, `test_fr_060_extract_json_fences_and_noise`.
- [x] FR-063: `test_fr_063_scripted_and_rule_based_without_network`, `test_fr_063_make_chat_provider_selection`, `test_fr_026_fr_063_cost_and_fake_provider_resync`.

## Tests and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
........................................................................ [ 71%]
.............................                                            [100%]
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
src/lodestone/connectors/__init__.py       0      0   100%
src/lodestone/connectors/files.py        132      6    95%   76, 92, 143-144, 152-153
src/lodestone/distill/__init__.py          5      0   100%
src/lodestone/distill/apply.py            93      3    97%   50, 65, 168
src/lodestone/distill/heuristic.py        63      7    89%   35-36, 42-45, 62
src/lodestone/distill/llm.py              27      1    96%   42
src/lodestone/distill/render.py           45      1    98%   67
src/lodestone/distill/schema.py           15      0   100%
src/lodestone/ingest/__init__.py           0      0   100%
src/lodestone/ingest/pipeline.py         109      1    99%   186
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
TOTAL                                   1563     66    96%
Required test coverage of 80% reached. Total coverage: 95.78%
101 passed in 9.94s
```

```text
$ ruff check .
All checks passed!

$ ruff format --check .
94 files already formatted

$ mypy --strict src
Success: no issues found in 30 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 55 Python files <= 500 lines, all SPDX headers present
```

## Authorship

Recorded after the feature commits on `feat/providers-distillation`:

```text
$ git log 376de6a..HEAD --format='%h %an <%ae> | %cn <%ce>'
3faf532 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
c1345ee Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
9e72cfb Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
4790aef Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log 376de6a..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## FakeLLM resync and cost

Temporary workspace `/tmp/lodestone-providers-demo`. Second `sync --provider fake` reports `llm_calls: 0`.

```text
$ lodestone init
Initialised lodestone.toml and database schema 3

$ lodestone source add docs --path docs --kind files
Added source: docs

$ lodestone sync --provider fake
{"processed": 1, "unchanged": 0, "skipped": 0, "llm_calls": 1, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 1, "cards_llm": 1, "cards_heuristic": 0}

$ lodestone sync --provider fake
{"processed": 0, "unchanged": 1, "skipped": 0, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 1, "cache_misses": 0, "cards_llm": 0, "cards_heuristic": 0}

$ lodestone cost
{
  "operations": [
    {
      "op": "card",
      "calls": 1,
      "in_tokens": 194,
      "out_tokens": 34,
      "ok": 1,
      "latency_ms": 0,
      "usd": 0.0
    }
  ],
  "total": {
    "calls": 1,
    "in_tokens": 194,
    "out_tokens": 34,
    "ok": 1,
    "latency_ms": 0,
    "usd": 0.0
  },
  "prices": {
    "input": 0.0,
    "output": 0.0,
    "as_of": null
  }
}
```

## CI

PR head `3faf532763ae073538a6547b71a68d788c15b52b`. All nine jobs `completed` / `success`.

```text
https://github.com/drkwv34/lodestone-kb/actions/runs/39147658411
conclusion: success
```

```json
{
  "url": "https://github.com/drkwv34/lodestone-kb/actions/runs/39147658411",
  "head_sha": "3faf532763ae073538a6547b71a68d788c15b52b",
  "status": "completed",
  "conclusion": "success",
  "jobs": [
    {"name": "lint-type", "status": "completed", "conclusion": "success"},
    {"name": "openspec", "status": "completed", "conclusion": "success"},
    {"name": "licenses", "status": "completed", "conclusion": "success"},
    {"name": "build", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.13)", "status": "completed", "conclusion": "success"},
    {"name": "test (macos-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.12)", "status": "completed", "conclusion": "success"},
    {"name": "test (ubuntu-latest, 3.11)", "status": "completed", "conclusion": "success"},
    {"name": "test (windows-latest, 3.12, true)", "status": "completed", "conclusion": "success"}
  ]
}
```
