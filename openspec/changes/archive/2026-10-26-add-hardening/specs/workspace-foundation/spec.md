# Spec Delta

## MODIFIED Requirements

### Requirement: FR-080 local diagnostics subset
The CLI SHALL implement "FR-080": report Python/SQLite versions, FTS5
availability, sqlite-vec availability, DB schema version, provider
reachability only if configured and not offline, and config problems; exit 1
if any error.

#### Scenario: FTS5 unavailable
- **WHEN** SQLite rejects FTS5 creation
- **THEN** doctor exits 1 with an FTS5 error and Python-build remediation

#### Scenario: sqlite-vec and provider probes
- **WHEN** doctor runs on a valid workspace
- **THEN** it reports sqlite-vec availability and, if a provider is configured
  and the workspace is not offline, probes reachability
