## 1. Providers
- [x] 1.1 Implement httpx chat client with retry/backoff and tolerant JSON extraction (FR-060).
- [x] 1.2 Implement FakeLLM scripted and rule-based modes (FR-063).
- [x] 1.3 Add a local fake HTTP server pytest fixture for 200/429/500/timeout/truncated bodies.

## 2. Distillation
- [x] 2.1 Add `prompts/card.v1.md`, card schema, LLM distiller with two JSON retries, then heuristic fallback (FR-020).
- [x] 2.2 Implement heuristic cards and golden fixtures (FR-021).
- [x] 2.3 Render `norm_text`, embedding input, and embed-source requeue (FR-022).
- [x] 2.4 Key card cache by content hash, prompt version and model (FR-023).
- [x] 2.5 Store provenance and return raw text from `get_record` (FR-024).
- [x] 2.6 Optional chunk `context_prefix` when `chunks.contextualize=true` (FR-025).

## 3. Retrieval, cost and ingest
- [x] 3.1 Add `fts_card` over `norm_text` and a paraphrase fixture (FR-031).
- [x] 3.2 Log every LLM call and add `lodestone cost` with a totals property test (FR-026).
- [x] 3.3 Wire sync `--provider fake`, `--refresh-cards`, and card application after structural upsert.

## 4. Verification
- [x] 4.1 Name tests with FR IDs; raise in-repo coverage gate to 80%; keep mypy, ruff, import-linter and module limits.
- [x] 4.2 Paste OpenSpec validation, tests, authorship, demo transcript and CI evidence; open a ready PR and do not merge.
