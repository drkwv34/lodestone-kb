# lexical-search Specification

## Purpose
Provide offline ingestion and lexical retrieval for local md/txt/rst corpora,
with jailed file discovery, hash-guarded record updates, transactional FTS and
document-frequency maintenance, and source/kind-filtered raw or rare-term search.

## Requirements

### Requirement: FR-010 local text files
The connector SHALL implement "FR-010" for md/txt/rst only on Day 2, matching
include/exclude globs and nested .gitignore rules, rejecting traversal and paths
resolving outside the source root, and logging skips for binaries and files over
max_file_bytes (default 1 MiB).

#### Scenario: Mixed fixture corpus
- **WHEN** sync discovers supported, ignored, excluded, binary and oversize files
- **THEN** only eligible UTF-8 text files become one doc record each and skips have reasons

#### Scenario: Jailed paths
- **WHEN** a path uses traversal, an absolute path, or a symlink outside the source root
- **THEN** no outside content is read or ingested

### Requirement: FR-014 hash skeleton
The ingest pipeline SHALL implement "FR-014" partially: stable (source_id, ext_id)
keys and SHA-256 of normalised raw text plus a versioned file chunker guard.

#### Scenario: Unchanged and edited files
- **WHEN** an unchanged corpus is synced again and then one file is edited
- **THEN** the second sync writes zero records and makes zero LLM calls, and the edit
  replaces only that file in place with its FTS and term statistics atomically

### Requirement: FR-030 safe raw lexical retrieval
The raw lane SHALL implement "FR-030" using FTS5 BM25 weights title=3.0, text=1.0,
Unicode-aware identifier-preserving tokens and a sanitiser supporting quoted
phrases, trailing prefix stars and literal-word OR expansion.

#### Scenario: Fuzz and exact identifier
- **WHEN** 1,000 arbitrary strings and ERR_MANIFEST_TIMEOUT are searched
- **THEN** no query raises an SQL error and the identifier-containing fixture ranks first

### Requirement: FR-032 rarity infrastructure
The system SHALL implement "FR-032" infrastructure with distinct raw/title term
document frequencies over active records, cached N, and
idf=ln(1+(N-df+0.5)/(df+0.5)); the fts_rare lane SHALL require at least one query
term satisfying rare_idf (default 4.0), or the configured rare_df_ratio override.

#### Scenario: Hand-computed frequencies
- **WHEN** records with repeated terms are inserted, changed, tombstoned or deleted
- **THEN** df counts records once, N counts active records, and IDF equals the hand calculation

#### Scenario: Rare term required
- **WHEN** a mixed filler/rare query is searched in fts_rare
- **THEN** only records matching a qualifying rare query term can be returned

### Requirement: FR-041 source and kind filters
The lexical lanes SHALL implement "FR-041" partially with parameterised source
name and record kind filters applied before ordering and limit.

#### Scenario: Filtered single-lane output
- **WHEN** a source/kind filter and limit are supplied to search
- **THEN** every returned hit satisfies both filters and identifies its selected lane
