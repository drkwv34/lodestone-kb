## Why

Local corpora need retrieval cards, a deterministic chat stand-in, and cost accounting so ingest can distill without a paid API. OpenAI-compatible chat, heuristic fallback, card cache, and an FTS card lane make those records searchable.

## What Changes

- Add an OpenAI-compatible chat client with retries, backoff, and JSON extraction (FR-060).
- Add deterministic FakeLLM for tests and `--provider fake` (FR-063).
- Distill `thread`, `doc`, and configurable `code_file` records into validated cards, with heuristic fallback, cache, provenance, and `norm_text` (FR-020, FR-021, FR-022, FR-023, FR-024).
- Optionally contextualize chunk records (FR-025).
- Index cards on the `fts_card` lane (FR-031) and summarise `llm_log` with `lodestone cost` (FR-026).

## Capabilities

### New Capabilities
- `providers-distillation`: chat providers, FakeLLM, card distillation, card cache, cost log, optional chunk context, and the `fts_card` lane.

### Modified Capabilities

## Impact

Extends ingest, lexical lanes, CLI (`sync --provider`, `--refresh-cards`, `cost`, `get`), configuration (`cards.norm_format`), and tests. Uses existing `card_cache` and `llm_log` tables; no paid APIs and no external network in tests.
