# Design

## Context

Schema version 2 already has `card_json`, `card_method`, `norm_text`, `card_cache`, and `llm_log`. Lexical ingest writes parent/child records and indexes `title`/`text` for `fts_raw`. Cards, providers, cost, and `fts_card` were not wired. Import direction remains `cli → workspace → ingest/lanes → distill → providers/storage`.

## Goals / Non-Goals

**Goals:**
- Distill cardable records during sync with cache, heuristic fallback, and provenance.
- Provide httpx chat with retries and a deterministic FakeLLM.
- Search `norm_text` on `fts_card` and summarise `llm_log` via `cost`.
- Keep tests free of paid APIs and external network.

**Non-Goals:**
- Embeddings backends, threads/bursts connectors, fusion, rerank-at-query, MCP, and `ask` (later work).
- Editing existing migrations or raising the schema version unless a new table is required.

## Decisions

- Reuse `card_cache` and `llm_log` from migration 0001. Migration 0003 adds
  `records_card_fts` and recreates `records_fts` over `title`/`text` only so
  card tokens cannot change raw BM25 or fail FTS integrity-check.
- Cache key is SHA-256 of `content_hash`, `prompt_version`, and `model` (`heuristic` when no chat client).
- Default sync without `--provider` uses heuristic cards (zero LLM calls) so
  unchanged-corpus tests stay at `llm_calls=0`. `--provider config` uses `[llm]`.
- `--provider fake` uses FakeLLM rule-based JSON; `card_method` is `llm` when validation succeeds.
- Chat retries: 429/5xx/timeout/unparseable body, base 0.5s, factor 2, jitter ±25%, `max_retries` extra attempts. Sleep and RNG are injectable for tests.
- JSON extraction strips fences and takes the outermost `{...}`. Distillation retries invalid JSON twice, then heuristic.
- `norm_text` follows FR-022; `cards.norm_format` selects `plain` or `xml`.
- `fts_card` uses column filter `{norm_text}` and BM25 weight on that column only.
- FakeLLM must not import `distill` (layering). Rule-based cards are a local JSON builder; FR-021 goldens use `HeuristicDistiller`.
- Changing `embed.source` deletes `embeddings` rows only; cards stay.
- Contextual prefixes (FR-025) apply to `section`/`code` children and are copied into empty `norm_text` so FTS can match them.

## Risks / Trade-offs

- Heuristic questions use the record title when present, which for files is the path stem; goldens pin that rule.
- Retry backoff is injectable so CI does not sleep real 0.5s intervals.
- Card writes are a second transaction after the structural upsert so a crash still leaves a raw-searchable record.
