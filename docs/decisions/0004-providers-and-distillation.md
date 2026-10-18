# Providers, FakeLLM and distillation cards

1. `card_cache` and `llm_log` already exist in migration 0001. Existing
   migrations are not edited. Migration 0003 adds `records_card_fts` and
   indexes `records_fts` without `norm_text` so card tokens do not change
   raw/title BM25. Schema version is 3.
2. Default sync without `[llm]` and without `--provider fake` writes heuristic
   cards and records zero LLM calls, so unchanged-corpus checks remain valid.
3. Cache keys hash `content_hash`, `prompt_version` and `model`. Heuristic-only
   runs use model name `heuristic`. FakeLLM uses its `model` attribute.
4. `fts_card` searches `records_card_fts` over `records.norm_text`. Raw/rare
   lanes keep using two-column `records_fts` (`title`, `text`).
5. `cards.norm_format` selects the FR-022 plain or XML `norm_text` renderer.
6. Changing `embed.source` deletes embedding rows only. Vector backends remain
   later work; the requeue path is covered by tests that insert placeholder rows.
