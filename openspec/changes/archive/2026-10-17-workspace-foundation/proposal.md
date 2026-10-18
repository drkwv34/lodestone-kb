## Why

The workspace foundation needs an installable, offline base before ingestion or
retrieval can be added. Preserve the five supplied specifications before implementation.

## What Changes

- Implement FR-001 workspace initialisation and FR-002 typed TOML configuration.
- Implement FR-082 forward-only migrations, architecture 7.1 without eval tables.
- Implement FR-080 partially: Python, SQLite, FTS5 and schema diagnostics only.
- Establish NFR-011 portability, NFR-012 initial gates (70% coverage, strict typing,
  Ruff, import boundaries, 500-line maximum), and NFR-017 Apache-2.0 licensing.
- Add config display redaction as the workspace-foundation FR-005 preview.

## Capabilities

### New Capabilities
- `workspace-foundation`: offline setup, configuration, schema and diagnostics.
- `repository-gates`: portability, quality and licensing checks.

### Modified Capabilities

None.

## Impact

New Python distribution `lodestone-kb`, CLI `lodestone`, SQLite schema v1, tests,
CI and repository documentation. No provider calls or paid APIs. Retrieval,
connectors, FTS triggers, vectors, MCP, SDK and benchmark execution are deferred.
