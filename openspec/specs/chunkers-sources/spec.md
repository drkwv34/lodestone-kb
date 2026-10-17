# chunkers-sources Specification

## Purpose
Define structural Markdown and code chunks, incremental file synchronization,
source management, project isolation, and environment-based secret configuration.

## Requirements

### Requirement: Structural document sections
The system SHALL implement "FR-015": split Markdown/text on headings then paragraphs, target 400 tokens, maximum 800 tokens, with configurable characters per token and heading paths as titles. Fences SHALL remain intact unless larger than the maximum.

#### Scenario: Nested headings and fenced content
- **WHEN** a document contains nested headings, paragraphs and fenced code
- **THEN** ordered section children retain correct heading paths and source spans, and each chunk satisfies the maximum

### Requirement: Coarse-to-fine code chunks
The system SHALL implement "FR-016" and "FR-010" code kinds with regex tables for py/js/ts/go/java/c/cpp/rs, signature outlines on code_file parents, and code children refined from class/struct through function/method to blocks.

#### Scenario: Oversized class and method
- **WHEN** a class contains a method whose if/for blocks exceed the chunk target together
- **THEN** deterministic ordered code chunks preserve the original text and enclosing symbol context

### Requirement: Complete incremental sync
The system SHALL implement "FR-014": stable source/ext_id parent identity, SHA-256 of normalized raw text and chunker version/settings, zero record writes for unchanged items, atomic child replacement, tombstones for missing files and purging with --prune.

#### Scenario: Edit, delete and restore
- **WHEN** one file changes, another disappears, and a tombstoned file returns
- **THEN** only changed files are reprocessed, disappeared records become unsearchable, returning files restore, and prune removes tombstoned records and dependent data

### Requirement: Source management
The system SHALL implement "FR-004" with source add/list/remove/sync and TOML registry persistence; removing a source SHALL purge records, FTS entries, embeddings and term contributions while retaining correct shared term frequencies.

#### Scenario: Remove one of two sources
- **WHEN** a source is removed
- **THEN** its configuration and project memberships disappear and shared term statistics count only retained records

### Requirement: Project scope
The system SHALL implement "FR-003": named source sets, a configurable default project, and --project scoping for search, sync and source commands. Explicit source filters SHALL intersect the selected project.

#### Scenario: Query isolated projects
- **WHEN** 200 generated queries run across disjoint projects
- **THEN** each result belongs to a source in the selected project, with filters applied before limits

### Requirement: Environment secret overrides
The system SHALL implement "FR-005": LODESTONE_LLM_API_KEY and LODESTONE_EMBED_API_KEY override configured secret environment references at runtime, without persistence; config show SHALL recursively redact keys matching key/token/secret.

#### Scenario: Secret override and safe output
- **WHEN** secret overrides are set and config show or source mutations run
- **THEN** runtime secret lookup sees the override and neither configuration output nor persisted TOML contains its value
