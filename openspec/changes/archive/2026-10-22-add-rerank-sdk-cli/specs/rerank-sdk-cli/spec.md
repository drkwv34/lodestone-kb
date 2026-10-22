# Spec Delta

## Purpose

Expose fused search through a typed SDK and polished CLI, with optional LLM
rerank, who-knows and recent retrieval, a privacy-preserving query log, and
documented OpenAI-compatible provider presets.

## ADDED Requirements

### Requirement: FR-039 LLM rerank
The system SHALL implement "FR-039": send the query plus top `candidate_pool` snippets (each at most 1,200 characters) to the chat model as JSON `[{id, score 0-10}]`, keep top `rerank_keep` (default 10), and on any error, timeout, or malformed output fall back to fused order with a notice.

#### Scenario: Valid reorder permutes the pool
- **WHEN** a FakeLLM returns a valid score list for the candidate pool
- **THEN** the reranked ids are a permutation of the input pool and sort by rerank score descending then fused score descending

#### Scenario: Malformed output keeps fused order
- **WHEN** no reranker is configured, the call fails, or the output is malformed
- **THEN** the returned order is identical to fused search without rerank and a notice is attached

### Requirement: FR-050 typed SDK facade
The system SHALL implement "FR-050": `Lodestone.open(path)` with `.sync()`, `.search()`, `.get()`, `.grep()`, `.who_knows()`, `.recent()`, `.stats()`, and a typed `.ask()`; the package is fully typed (`py.typed`) with no global state.

#### Scenario: mypy strict consumer
- **WHEN** a typed consumer imports `Lodestone` and calls the public methods
- **THEN** `mypy --strict` passes on that consumer

#### Scenario: README doctest
- **WHEN** the README SDK snippet is executed as a doctest
- **THEN** it completes without network or paid APIs

### Requirement: FR-051 CLI polish
The system SHALL implement "FR-051" for non-bench, non-MCP, non-ask commands: `search`, `grep`, `get`, `who-knows`, `recent`, and `stats` have consistent help and human/`--json` output; exit 0 on success, 1 runtime, 2 usage/config, 3 provider error.

#### Scenario: Help snapshots
- **WHEN** each of those commands is invoked with `--help`
- **THEN** the help text matches the stored snapshot

#### Scenario: Commands succeed in a workspace
- **WHEN** a fixture workspace is synced offline
- **THEN** `search`, `grep`, `get`, `who-knows`, `recent`, and `stats` exit 0

### Requirement: FR-043 who-knows
The system SHALL implement "FR-043": `who_knows(topic)` ranks authors by in-scope records matching the topic, weighted by recency and burst or reaction presence, and returns the top 5 with example record ids.

#### Scenario: Known expert is top-1
- **WHEN** a fixture with a known expert is queried for that topic
- **THEN** the expected author is rank 1 and includes example record ids

### Requirement: FR-044 recent records
The system SHALL implement "FR-044": `recent(n, since, filters)` returns the most recent in-scope records in deterministic order.

#### Scenario: Deterministic ordering
- **WHEN** two records differ only by `updated_at` and id
- **THEN** recent returns them by `updated_at` descending then id descending

### Requirement: FR-081 query log
The system SHALL implement "FR-081": a query log stores query hash, project, lanes, latency, and result count; query text is stored only if `log.store_queries=true`; `stats` reports workspace counts.

#### Scenario: Default stores no query text
- **WHEN** search runs with default `log.store_queries=false`
- **THEN** the query_log row has a hash and null query text

### Requirement: FR-064 provider presets
The system SHALL implement "FR-064": documentation includes Cerebras, OpenAI, and Ollama config examples with no provider-specific code paths except the optional `response_format` flag.

#### Scenario: Preset snippets validate
- **WHEN** each documented preset TOML snippet is loaded
- **THEN** it validates against the config schema
