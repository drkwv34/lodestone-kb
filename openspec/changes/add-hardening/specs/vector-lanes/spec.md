# Spec Delta

## MODIFIED Requirements

### Requirement: Offline provider swap
The system SHALL implement "FR-062": `--offline` / `offline=true` replaces
providers with the hash embedder and heuristic cards. Any attempt to use a
remote provider raises `OfflineError`. Full ingest, search, and bench of
offline strategies SHALL succeed with sockets patched to raise.

#### Scenario: Socket patched ingest and search
- **WHEN** sockets are patched to raise and sync plus search run with `--offline`
- **THEN** ingest and search succeed using the hash embedder

#### Scenario: Socket patched offline bench
- **WHEN** sockets are patched to raise and offline bench strategies run
- **THEN** the run completes with no outbound network

### Requirement: Vec reindex
The system SHALL implement "FR-083": `reindex --lanes fts|vec|cards` rebuilds
derived data from stored raw text without re-contacting sources, and row counts
on a fixture SHALL be identical before and after.

#### Scenario: Identical counts
- **WHEN** `reindex --lanes vec` runs on an already-embedded fixture
- **THEN** embedding and record counts match the counts taken before reindex and sources are not contacted

#### Scenario: FTS and cards rebuild
- **WHEN** `reindex --lanes fts` or `reindex --lanes cards` runs on a fixture
- **THEN** FTS or card row counts match the counts taken before reindex and sources are not contacted
