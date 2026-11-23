# Spec Delta

## MODIFIED Requirements

### Requirement: Coarse-to-fine code chunks
The system SHALL implement "FR-016" and "FR-010" code kinds with regex tables for py/js/ts/go/java/c/cpp/rs, signature outlines on code_file parents, and code children refined from class/struct through function/method to blocks. Detected blocks under a method SHALL become children even when that method is under `target_tokens`. Outlines SHALL omit block-level symbols.

#### Scenario: Oversized class and method
- **WHEN** a class contains a method whose if/for blocks exceed the chunk target together
- **THEN** deterministic ordered code chunks preserve the original text and enclosing symbol context

#### Scenario: Figure fixture under default limits
- **WHEN** `tests/fixtures/chunking/figure.code` is chunked as Python with default `target_tokens` and `max_tokens`, titled `processor`
- **THEN** the ordered `{title, text}` chunks equal `tests/fixtures/chunking/figure.json`, including `processor > Processor > run > if` and `processor > Processor > run > for`

#### Scenario: Chunker version rewrite
- **WHEN** an already-ingested code file is synced after the code chunker version changes
- **THEN** the parent `content_hash` changes, children are replaced atomically, and `derived_state` is pending until cards/embeddings catch up
