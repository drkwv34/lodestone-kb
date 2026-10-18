# providers-distillation Specification

## Purpose
Provide OpenAI-compatible and fake chat providers, distill records into cached retrieval cards with heuristic fallback, account for call cost, and search cards on an FTS lane.

## Requirements

### Requirement: Structured LLM cards
The system SHALL implement "FR-020": for `thread`, `doc` and configurable `code_file` records, call the chat model with versioned prompt `prompts/card.v1.md`, validate JSON `{question, summary, resolution, entities[], code_refs[]}`, retry invalid JSON up to 2 times, then fall back to FR-021.

#### Scenario: Recover after two malformed payloads
- **WHEN** FakeLLM returns malformed JSON twice then valid JSON
- **THEN** the stored card matches the valid payload and `card_method` is `llm`

#### Scenario: Fallback after three malformed payloads
- **WHEN** FakeLLM returns malformed JSON three times
- **THEN** a heuristic card is stored and `card_method` is `heuristic`

### Requirement: Heuristic cards
The system SHALL implement "FR-021": question is title or the first `?` sentence else the first line; summary is the first two sentences clipped to 300 characters; resolution is the last thread message or empty; entities are the top five capitalised or identifier-like terms by IDF; code_refs match the specified identifier, path and error-code patterns. Output SHALL be deterministic with zero network.

#### Scenario: Golden fixtures
- **WHEN** heuristic cards are built from the checked-in fixtures
- **THEN** JSON matches the golden files

### Requirement: Card norm text and embedding input
The system SHALL implement "FR-022": `norm_text` is `question`, `summary`, `resolution`, `systems:` entities and `code:` code_refs joined by newlines, with an XML-tagged variant selectable. When a card exists and `embed.source` is `card`, raw text SHALL NOT be the embedding input. Changing `embed.source` SHALL re-queue embeddings only.

#### Scenario: Plain norm text and card-only embed input
- **WHEN** a card is rendered with default `embed.source=card`
- **THEN** embedding input equals `norm_text` and excludes raw text

#### Scenario: Embed source change
- **WHEN** `embed.source` changes on an otherwise unchanged corpus
- **THEN** embeddings are cleared and cards plus record bodies stay in place

### Requirement: Card cache
The system SHALL implement "FR-023": cache keys are `(content_hash, prompt_version, model)`. Regeneration happens only on `--refresh-cards` or key mismatch.

#### Scenario: Unchanged rerun hits cache
- **WHEN** ingest reruns with the same model and prompt version
- **THEN** cache hit ratio is 100% and no new LLM calls are made for those records

#### Scenario: Model change regenerates
- **WHEN** the model in the cache key changes
- **THEN** regeneration count equals the number of cardable records

### Requirement: Card provenance
The system SHALL implement "FR-024": every card stores `source_message_ids` or character spans, and `get_record` returns raw text beside the card.

#### Scenario: Checkable claims
- **WHEN** cards are produced for a fixture corpus
- **THEN** every card has provenance and `get_record` includes `raw_text` next to the card

### Requirement: Chunk contextual prefix
The system SHALL implement "FR-025": when `chunks.contextualize=true`, chunk records store a 50-100 token context in `context_prefix` that is FTS-matchable.

#### Scenario: Prefix searchable
- **WHEN** FakeLLM supplies a unique context prefix under `chunks.contextualize=true`
- **THEN** that prefix is stored and found in FTS-matchable text

### Requirement: Cost accounting
The system SHALL implement "FR-026": every LLM call is logged with tokens in/out, latency and model; `lodestone cost` summarises per operation from a configurable price table.

#### Scenario: Totals match the log
- **WHEN** cost is summarised over arbitrary `llm_log` rows
- **THEN** reported totals equal the sum of those rows

### Requirement: OpenAI-compatible chat client
The system SHALL implement "FR-060": an httpx client with base URL, model, API key environment, timeout, exponential backoff with jitter, JSON mode when supported, and tolerant JSON extraction, tested against a local fake HTTP server.

#### Scenario: Fault injection
- **WHEN** the local server returns 200, 429, 500, timeout or a truncated body
- **THEN** success, retry, or failure follows the retry policy without contacting a paid API

### Requirement: FakeLLM
The system SHALL implement "FR-063": deterministic FakeLLM with scripted replies and rule-based cards, rerank-by-overlap and default planner output, used in tests and `--provider fake`, with no network.

#### Scenario: Scripted and rule-based modes
- **WHEN** unit and ingest tests run with FakeLLM
- **THEN** behaviour is deterministic and no outbound network is used

### Requirement: Card FTS lane
The system SHALL implement "FR-031": lane `fts_card` runs FTS5 over `norm_text`.

#### Scenario: Paraphrase only in the card
- **WHEN** a paraphrase query shares tokens with the card and not the raw text
- **THEN** `fts_card` finds the record and `fts_raw` does not
