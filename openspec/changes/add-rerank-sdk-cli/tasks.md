# Tasks

## 1. Rerank stage

- [x] 1.1 Add `lodestone.rerank` and extend import-linter so rerank sits with fusion; verify `test_fr_039_rerank_permutes_candidate_pool`.
- [x] 1.2 Fall back to fused order when no reranker is configured or the model errors/returns malformed JSON; verify `test_fr_039_rerank_fallback_keeps_fused_order`.
- [x] 1.3 Apply rerank to the collapsed pool before neighbour expansion and fill `explain.rerank_score`; verify `test_fr_039_explain_includes_rerank_score`.

## 2. Query log, who-knows and recent

- [x] 2.1 Write `query_log` rows (hash, project, lanes, latency, result count) with text only when `log.store_queries=true`; verify `test_fr_081_default_query_log_stores_no_text`.
- [x] 2.2 Implement `who_knows(topic)` ranking authors by matching records weighted by recency and burst/reaction presence; verify `test_fr_043_who_knows_returns_expected_top_expert`.
- [x] 2.3 Implement `recent(n, since, filters)` with deterministic `updated_at` then id ordering; verify `test_fr_044_recent_deterministic_order`.

## 3. SDK, CLI and docs

- [x] 3.1 Add the typed `Lodestone` facade, ship `py.typed`, and run the README snippet as a doctest; verify `test_fr_050_sdk_mypy_strict` and `test_fr_050_readme_doctest`.
- [x] 3.2 Add CLI `grep`, `who-knows`, `recent`, `stats`, and `--rerank` on search with consistent help/JSON; verify `test_fr_051_cli_help_snapshots` and `test_fr_051_search_grep_get_who_knows_recent_stats`.
- [x] 3.3 Document Cerebras, OpenAI and Ollama presets and validate the snippets; verify `test_fr_064_provider_preset_snippets_validate`.

## 4. Integration checks

- [x] 4.1 Run `openspec validate add-rerank-sdk-cli --strict`, ruff, mypy --strict, import-linter, module-size gate, and pytest with coverage >= 80%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
