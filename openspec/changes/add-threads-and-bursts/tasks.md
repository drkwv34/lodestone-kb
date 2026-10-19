## 1. Connector and example

- [x] 1.1 Stream JSONL threads, skip malformed lines with line numbers, parse timestamps to UTC (FR-011).
- [x] 1.2 Add `examples/slack_export_to_jsonl.py` converting a Slack export fixture to the FR-011 shape.

## 2. Ingest, bursts and cards

- [x] 2.1 Render one `kind=thread` record per thread and replace record, card, bursts and embeddings atomically on change (FR-012).
- [x] 2.2 Group consecutive same-author messages, score with configurable SRS defaults, store `context_prefix` (FR-013).
- [x] 2.3 Distill thread records through the existing provider/heuristic card path (FR-020, FR-021).

## 3. Verification

- [x] 3.1 Name tests with FR IDs: malformed JSONL, timezones, Cerebras five-message burst table, in-place append, searchable bursts, Slack example, thread cards.
- [x] 3.2 Keep coverage >= 80%, mypy --strict, ruff, import-linter and the 500-line module gate.
