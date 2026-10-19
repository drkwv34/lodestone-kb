## Why

Conversational exports need to enter the same record table as documents so search can retrieve a whole thread, a high-signal author run, and a distilled card. File ingestion already lands parents and children; JSONL threads, atomic whole-thread replace, and the burst gate are the remaining ingest path.

## What Changes

- Add a `threads` connector that streams JSONL, skips malformed lines with line numbers, and parses message timestamps to UTC (FR-011).
- Treat each thread as one `kind=thread` record; a changed thread replaces the record, card, bursts and embeddings in one transaction while keeping `id` (FR-012).
- Group consecutive same-author messages into bursts and index a burst only when its weighted IDF/length/reaction score meets the configured threshold; store the thread title or question as `context_prefix` (FR-013).
- Run thread records through the existing provider and distillation card path, including heuristic last-message resolution, with FakeLLM in tests (FR-020, FR-021).
- Add `examples/slack_export_to_jsonl.py` to convert a Slack export directory into the FR-011 JSONL shape.

## Capabilities

### New Capabilities
- `threads-bursts`: JSONL thread ingest, whole-thread upsert, burst scoring, and thread cards.

### Modified Capabilities

## Impact

Extends connectors, ingest, distillation input (thread messages), CLI `sync` for `kind=threads`, tests and examples. Existing schema already allows `thread` and `burst` kinds; no paid APIs and no network in tests.
