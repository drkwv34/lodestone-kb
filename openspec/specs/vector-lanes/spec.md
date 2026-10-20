# vector-lanes Specification

## Purpose
Optional embeddings, vector backends and vec retrieval lanes so search can use dense similarity when configured and still run fully offline with the hash embedder.

## Requirements

### Requirement: Embedder interface
The system SHALL implement "FR-061": an embedder interface `embed(list[str]) -> list[list[float]]` with implementations `openai_compat` and `hash`.

#### Scenario: Protocol shape
- **WHEN** an embedder is invoked with a list of strings
- **THEN** it returns one float vector per input string in the same order

### Requirement: Hash embedder
The system SHALL implement the `hash` embedder as deterministic signed feature hashing of tokens and bigrams, dimension 256, L2-normalised, documented as not semantic, for tests and offline demos only.

#### Scenario: Determinism
- **WHEN** the same text is embedded in separate runs
- **THEN** the vectors are identical, including a fixed expected prefix used by tests

### Requirement: OpenAI-compatible embedder
The system SHALL implement `openai_compat` over the existing httpx client with the chat retry policy and one `llm_log` row per attempt.

#### Scenario: Local fake HTTP server
- **WHEN** a local server returns success after a retryable failure
- **THEN** embeddings are returned and `llm_log` contains the attempts
- **WHEN** tests run
- **THEN** no paid API and no external network are used

### Requirement: Vector backends
The system SHALL implement "FR-033" storage via sqlite-vec when importable, else exact brute-force cosine (stdlib array plus dot product, numpy if installed). Both backends SHALL return the same results within 1e-6 on 1,000 vectors. sqlite-vec tests SHALL skip, not fail, when the extra is absent.

#### Scenario: Parity
- **WHEN** 1,000 vectors are queried on both backends
- **THEN** cosine scores agree within 1e-6
- **WHEN** sqlite-vec is not installed
- **THEN** that backend test is skipped

### Requirement: Embedding writes and lifecycle
The system SHALL write embeddings for card, chunk and burst records in the derived-data transaction keyed by content_hash, as float32 little-endian BLOBs. Embeddings SHALL be removed with their records, including on thread change.

#### Scenario: Ingest writes kinds
- **WHEN** a source is synced with embeddings enabled
- **THEN** card, chunk and burst embeddings exist for the corresponding records

#### Scenario: Deleted with records
- **WHEN** a record is deleted or a thread changes
- **THEN** its embeddings are gone and replacement embeddings match the new content

### Requirement: Model and dimension mismatch
The system SHALL treat embeddings whose model or dimension does not match the configured embedder as missing, emit a notice, and skip vec lanes until `reindex --lanes vec` rebuilds them.

#### Scenario: Mismatch notice
- **WHEN** stored embeddings use a different model or dimension than the current embedder
- **THEN** vec lanes are skipped with a notice until reindexed

### Requirement: Vector retrieval lanes
The system SHALL provide optional lanes `vec_card` and `vec_chunk` using the configured embedder. When embeddings are disabled or unavailable, those lanes SHALL be skipped and a notice SHALL appear in `result.notices`.

#### Scenario: Vec card hit
- **WHEN** embeddings are enabled and a query is close to a card vector
- **THEN** `vec_card` ranks that record

#### Scenario: Disabled skip
- **WHEN** embeddings are disabled or unavailable
- **THEN** `vec_card` and `vec_chunk` return no hits and `result.notices` names the skipped lanes

### Requirement: Offline provider swap
The system SHALL implement "FR-062" partially: `--offline` / `offline=true` replaces providers with the hash embedder and heuristic cards so ingest and search succeed with no outbound network.

#### Scenario: Socket patched ingest and search
- **WHEN** sockets are patched to raise and sync plus search run with `--offline`
- **THEN** ingest and search succeed using the hash embedder

### Requirement: OfflineError on remote attempts
The system SHALL raise `OfflineError` on any attempt to use a remote embedder or chat provider while offline.

#### Scenario: Remote embedder refused
- **WHEN** a remote embedder or provider is invoked while offline
- **THEN** `OfflineError` is raised before a network call

### Requirement: Vec reindex
The system SHALL implement "FR-083" for vec: `reindex --lanes vec` rebuilds embeddings from stored text without contacting sources, and row counts on a fixture SHALL be identical before and after.

#### Scenario: Identical counts
- **WHEN** `reindex --lanes vec` runs on an already-embedded fixture
- **THEN** embedding and record counts match the counts taken before reindex and sources are not contacted
