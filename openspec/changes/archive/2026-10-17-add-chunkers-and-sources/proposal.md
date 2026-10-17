## Why

Local document and code collections need structural chunks, reliable incremental updates, and explicit source boundaries for project queries.

## What Changes

- Add heading-aware Markdown/text sections and regex code chunking for eight languages.
- Store file parents and ordered section/code children with versioned content hashes.
- Tombstone missing files, restore returning files, and purge with `sync --prune`.
- Add source registry commands and validated project scopes in configuration and CLI.
- Resolve secret overrides from environment variables and redact configuration output.

## Capabilities

### New Capabilities
- `chunkers-sources`: FR-015, FR-016, FR-014, FR-003, FR-004, FR-005 and FR-010 code kinds.

### Modified Capabilities

## Impact

Extends existing ingestion, file discovery, configuration, workspace operations and CLI. Existing schema already supports hierarchy, tombstones and project membership; migrations remain immutable. All operations work locally without paid APIs.
