# Spec Delta

## Purpose

Ingest JSONL conversation threads as whole-thread records with gated same-author bursts and distilled cards.

## ADDED Requirements

### Requirement: JSONL threads connector
The system SHALL implement "FR-011": the `threads` connector reads JSONL with one object per thread `{thread_id, channel?, title?, messages:[{id, author, ts(ISO-8601), text, reactions?:int}]}` and accepts a Slack-export-to-JSONL helper in `examples/`. Malformed lines SHALL be skipped with line numbers reported; valid lines SHALL be ingested; `ts` SHALL be parsed to UTC.

#### Scenario: Malformed lines skipped
- **WHEN** a JSONL file mixes valid thread objects with invalid JSON and incomplete objects
- **THEN** invalid lines are skipped, each skip names its line number, and valid threads are ingested

#### Scenario: Timestamp conversion
- **WHEN** a message `ts` uses `Z` or a numeric offset
- **THEN** the stored timestamp is UTC
- **WHEN** a message `ts` is timezone-naive
- **THEN** that line is skipped

#### Scenario: Slack export helper
- **WHEN** `examples/slack_export_to_jsonl.py` runs on a small Slack export fixture
- **THEN** the output is FR-011 JSONL that the threads connector ingests

### Requirement: Whole-thread upsert
The system SHALL implement "FR-012": a thread is ONE record `kind=thread`; re-ingesting a changed thread replaces the record, its card, its bursts and embeddings atomically in one transaction.

#### Scenario: Append updates in place
- **WHEN** a message is appended to a previously ingested thread and the source is synced
- **THEN** `id` is unchanged, `updated_at` and `content_hash` change, and old bursts are removed

### Requirement: Burst records and scoring gate
The system SHALL implement "FR-013": consecutive same-author messages form a burst; a burst is indexed iff `score >= threshold` using the SRS weighted IDF, length and reaction formula and defaults. Defaults SHALL be configurable in Config. Bursts SHALL store the thread title or question as `context_prefix`. Indexed bursts SHALL be `kind=burst` children searchable on existing lexical lanes.

#### Scenario: Cerebras five-message figure
- **WHEN** the five-message example is scored with `score = w_idf*[max_token_idf >= idf_min] + w_len*[chars >= min_chars] + w_react*[reactions>=1]` and defaults `idf_min=4.0, min_chars=200, w_idf=1, w_len=1, w_react=1, threshold=1.0`
- **THEN** the short common-token burst is filtered and the long rare-term reacted-to burst is kept
- **WHEN** thresholds are raised so no single signal passes
- **THEN** that long burst is also filtered

#### Scenario: Burst search
- **WHEN** a qualifying burst contains a distinctive token
- **THEN** `search` with `kind=burst` returns that child record

### Requirement: Thread distillation cards
The system SHALL apply "FR-020" and "FR-021" to `kind=thread` records through the existing provider and distillation card path. FakeLLM SHALL be used in tests. Heuristic resolution SHALL be the last message of the thread.

#### Scenario: FakeLLM thread card
- **WHEN** a thread is synced with FakeLLM
- **THEN** a card is stored on the thread record and `card_method` is `llm` or `heuristic` according to the provider result

#### Scenario: Heuristic last message
- **WHEN** a thread is synced without a chat provider
- **THEN** the heuristic card `resolution` equals the last message text
