# Optional embeddings, vector backends and vec lanes

Feature base: `main` at `417dc271826186d2ac2434d22bad3f8ae0d5118a`.
Branch: `feat/vector-lanes`.
OpenSpec change: `add-vector-lanes`.
Existing migrations were not edited. Schema version remains 3. Embeddings table already exists.

## OpenSpec

```text
$ openspec --version
1.14.3

$ openspec validate add-vector-lanes --strict
Change 'add-vector-lanes' is valid

$ openspec validate --all --strict
✓ change/add-vector-lanes
✓ spec/chunkers-sources
✓ spec/lexical-search
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/threads-bursts
✓ spec/workspace-foundation
Totals: 7 passed, 0 failed (7 items)
```

```text
$ openspec list
Changes:
  add-vector-lanes     ✓ Complete
```

Archive after merge as a direct commit on main; not in this run.

## Requirement checklist

- [x] FR-033: `test_fr_033_backend_parity_1000_vectors`, `test_fr_033_sqlite_vec_backend_present`, `test_fr_033_embeddings_deleted_with_records_and_replaced_on_thread_change`, `test_fr_033_model_dim_mismatch_treated_as_missing`, `test_fr_033_vec_lanes_skipped_with_notice_when_disabled`, `test_fr_033_vec_card_and_chunk_hits`, `test_fr_033_pack_unpack_and_backend_edges`, `test_fr_033_fr_083_workspace_search_result_and_reindex`, `test_fr_033_fr_062_fr_083_offline_search_reindex_and_disabled_notice`.
- [x] FR-061: `test_fr_061_hash_embedder_deterministic`, `test_fr_061_openai_compat_embedder_retry_and_llm_log`, `test_fr_061_make_embedder_offline_hash_and_providers`.
- [x] FR-062 partial (hash swap + OfflineError on remote attempts): `test_fr_062_offline_guard_hash_embedder_and_remote_raises`, `test_fr_033_fr_062_fr_083_offline_search_reindex_and_disabled_notice`.
- [x] FR-083 vec: `test_fr_083_reindex_lanes_vec_row_counts_identical`, `test_fr_033_fr_083_workspace_search_result_and_reindex`, `test_fr_033_fr_062_fr_083_offline_search_reindex_and_disabled_notice`.

## Tests and coverage

```text
$ pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
........................................................................ [ 50%]
.......................................................................  [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
src/lodestone/__init__.py                    1      0   100%
src/lodestone/chunking/__init__.py          34      1    97%   30
src/lodestone/chunking/code.py              92      2    98%   95, 108
src/lodestone/chunking/markdown.py          53      0   100%
src/lodestone/cli.py                       198     33    83%   79, 96, 125-126, 139-141, 158-160, 196-197, 199-200, 212, 222, 224-228, 254-255, 268-270, 342-348
src/lodestone/config.py                    189      0   100%
src/lodestone/config_io.py                  36      3    92%   18, 20, 35
src/lodestone/connectors/__init__.py         3      0   100%
src/lodestone/connectors/files.py          140      6    96%   86, 102, 153-154, 162-163
src/lodestone/connectors/threads.py        102      0   100%
src/lodestone/distill/__init__.py            5      0   100%
src/lodestone/distill/apply.py             113     10    91%   51, 66, 151-152, 158-161, 163, 206
src/lodestone/distill/heuristic.py          63      7    89%   35-36, 42-45, 62
src/lodestone/distill/llm.py                27      1    96%   42
src/lodestone/distill/render.py             45      1    98%   67
src/lodestone/distill/schema.py             15      0   100%
src/lodestone/ingest/__init__.py             0      0   100%
src/lodestone/ingest/bursts.py              38      0   100%
src/lodestone/ingest/embeddings.py          49      0   100%
src/lodestone/ingest/pipeline.py           173     10    94%   63, 142-157, 285-286, 289
src/lodestone/lanes/__init__.py              5      0   100%
src/lodestone/lanes/fts.py                  65      0   100%
src/lodestone/lanes/result.py                8      0   100%
src/lodestone/lanes/vec.py                  56      2    96%   44, 111
src/lodestone/providers/__init__.py         28      0   100%
src/lodestone/providers/chat.py            110      5    95%   116, 134, 149, 153, 177
src/lodestone/providers/fake.py             69      6    91%   63-67, 74
src/lodestone/providers/offline.py          19      0   100%
src/lodestone/storage/__init__.py            0      0   100%
src/lodestone/storage/costs.py              23      0   100%
src/lodestone/storage/db.py                 58      1    98%   31
src/lodestone/storage/embeddings.py         18      0   100%
src/lodestone/storage/records.py            20      2    90%   22-23
src/lodestone/storage/registry.py           28      2    93%   32, 47
src/lodestone/storage/terms.py              17      0   100%
src/lodestone/tokenize.py                   10      0   100%
src/lodestone/vectors/__init__.py            6      0   100%
src/lodestone/vectors/backends.py           86     10    88%   22-23, 35-36, 44-45, 66, 80-81, 115
src/lodestone/vectors/embedder.py           19      0   100%
src/lodestone/vectors/hash.py               32      0   100%
src/lodestone/vectors/openai_compat.py      97      8    92%   97, 103, 112-113, 116, 125, 148, 163
src/lodestone/workspace.py                 126      5    96%   31-32, 88, 153, 206
----------------------------------------------------------------------
TOTAL                                     2276    115    95%
Required test coverage of 80% reached. Total coverage: 94.95%
143 passed in 12.30s
```

```text
$ ruff check .
All checks passed!

$ ruff format --check .
142 files already formatted

$ mypy --strict src
Success: no issues found in 42 source files

$ lint-imports --config importlinter.ini
Contracts: 2 kept, 0 broken.

$ python3 scripts/check_modules.py
Module gate: 75 Python files <= 500 lines, all SPDX headers present
```

## Authorship

Recorded after the feature commits on `feat/vector-lanes`:

```text
$ git log 417dc27..HEAD --format='%h %an <%ae> | %cn <%ce>'
12ececc Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
1dbd779 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
634204e Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f4041c1 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
0b9470b Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
74cfc5f Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
f574bd0 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
be39c85 Christian Agila <87576768+drkwv34@users.noreply.github.com> | Christian Agila <87576768+drkwv34@users.noreply.github.com>
```

```text
$ git log 417dc27..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'
0
```

## Demo

Temporary workspace `/tmp/tmp.VJCNlm8DiF` with `tests/fixtures/corpus`.

```text
$ lodestone init
Initialised lodestone.toml and database schema 3

$ lodestone sync --offline
Skipping binary.txt: binary
Skipping ignored.txt: ignored
Skipping unsupported.csv: unsupported extension
Skipping drafts/draft.md: ignored
Skipping nested/hidden.txt: ignored
{"processed": 4, "unchanged": 0, "skipped": 5, "llm_calls": 0, "tombstoned": 0, "pruned": 0, "cache_hits": 0, "cache_misses": 4, "cards_llm": 0, "cards_heuristic": 4}

$ lodestone search "ERR_MANIFEST_TIMEOUT" --lane vec_card --offline --explain --json
{"lane": "vec_card", "hits": [{"id": 5, "ext_id": "manifest.md", "source": "wiki", "kind": "doc", "title": "manifest", "uri": "file:///tmp/tmp.VJCNlm8DiF/corpus/manifest.md", "snippet": "# Manifest restore ERR_MANIFEST_TIMEOUT occurs when restoring a checkpoint over NFS. Set CKPT_PREFETCH=4 and retry the manifest load. ", "score": 0.22792112827301025, "lane": "vec_card", "updated_at": "2026-10-19T18:04:04.431806+00:00"}, {"id": 7, "ext_id": "nested/keep.txt", "source": "wiki", "kind": "doc", "title": "keep", "uri": "file:///tmp/tmp.VJCNlm8DiF/corpus/nested/keep.txt", "snippet": "A nested gitignore negation keeps this handbook. ", "score": 0.0, "lane": "vec_card", "updated_at": "2026-10-19T18:04:04.431806+00:00"}, {"id": 3, "ext_id": "guide.rst", "source": "wiki", "kind": "doc", "title": "guide", "uri": "file:///tmp/tmp.VJCNlm8DiF/corpus/guide.rst", "snippet": "Caf\u00e9 operations =============== Unicode identifiers: na\u00efve fa\u00e7ade \u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac \u6771\u4eac camelCase snake_case ERR_OTHER-42. ", "score": 0.0, "lane": "vec_card", "updated_at": "2026-10-19T18:04:04.431806+00:00"}, {"id": 1, "ext_id": "chatter.txt", "source": "wiki", "kind": "doc", "title": "chatter", "uri": "file:///tmp/tmp.VJCNlm8DiF/corpus/chatter.txt", "snippet": "sounds good, thanks The manifest restore timeout is a common topic in the daily discussion. ", "score": 0.0, "lane": "vec_card", "updated_at": "2026-10-19T18:04:04.431806+00:00"}], "notices": [], "explain": [{"id": 5, "lane": "vec_card", "rank": 1, "score": 0.22792112827301025}, {"id": 7, "lane": "vec_card", "rank": 2, "score": 0.0}, {"id": 3, "lane": "vec_card", "rank": 3, "score": 0.0}, {"id": 1, "lane": "vec_card", "rank": 4, "score": 0.0}]}

$ lodestone reindex --lanes vec --offline
{"before": 8, "after": 8, "written": 8, "records": 8}

$ lodestone search "ERR_MANIFEST_TIMEOUT" --lane vec_card --json
{"lane": "vec_card", "hits": [], "notices": ["vec_card skipped: embeddings disabled"]}
```

`--offline` used the hash embedder (no `embed.provider` in the default TOML). `vec_card` ranked `manifest.md` first. Reindex counts matched. Without `--offline`, the lane was skipped with a notice.

## CI

Pending green checks on the PR head. This section will be pasted from the GitHub Actions run once it completes.
