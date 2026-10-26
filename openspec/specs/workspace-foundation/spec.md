# workspace-foundation Specification

## Purpose
Provide a repeatable local workspace with validated configuration, safe schema
upgrades and runtime diagnostics before ingestion and retrieval are introduced.

## Requirements

### Requirement: FR-001 workspace initialisation
The CLI SHALL implement "FR-001": `lodestone init [PATH]` creates lodestone.toml
and .lodestone/index.db stamped with the current schema version.

#### Scenario: Repeat initialisation
- **WHEN** init runs twice in the same workspace
- **THEN** both runs exit 0, the second prints "already initialised", and existing
  configuration and data are preserved

### Requirement: FR-002 configuration validation
The system SHALL implement "FR-002": TOML configuration is validated by pydantic,
unknown keys are rejected, and paths resolve relative to the config file.

#### Scenario: Five invalid configuration fixtures
- **WHEN** an invalid config contains a wrong source kind, unknown key, unknown
  weight lane, invalid token ratio, or unsupported schema version
- **THEN** the CLI exits 2 and reports the failing path, including sources[0].kind
  for an invalid source kind, without exposing secret input values

### Requirement: FR-082 schema migrations
The storage layer SHALL implement "FR-082": forward-only numbered migrations
apply transactionally and opening a newer schema fails before mutation.

#### Scenario: Apply or refuse migration
- **WHEN** an empty database is opened
- **THEN** schema v1 is created without eval tables and stamped atomically

#### Scenario: Failed migration rolls back
- **WHEN** a migration contains invalid SQL after a DDL statement
- **THEN** neither its DDL nor its version stamp is committed

#### Scenario: Newer database refuses downgrade
- **WHEN** a database stamped above the supported version is opened
- **THEN** a clear newer-schema error is returned and the database is preserved

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

### Requirement: FR-005 secret redaction preview
The CLI SHALL preview "FR-005" by recursively redacting config-show fields whose
names contain key, token or secret, without resolving environment values.

#### Scenario: Display configured provider
- **WHEN** a provider environment variable contains a secret
- **THEN** config show prints [REDACTED] and never prints the secret value
