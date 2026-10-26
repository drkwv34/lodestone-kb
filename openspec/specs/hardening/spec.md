# hardening Specification

## Purpose
Harden plugin connectors, bounded ingest concurrency, crash-safe derived data,
structured logs, security jails, provider degradation, and lexical scale so the
engine stays local, consistent, and observable.

## Requirements

### Requirement: FR-017 connector plugin API
The system SHALL load connectors from the `lodestone.connectors` entry-point
group. `discover(config)` SHALL yield items with `ext_id`, `kind_hint`, `text`,
`metadata`, and `updated_at`. A documented example plugin SHALL be at most 60
lines.

#### Scenario: Example plugin loads through entry points
- **WHEN** an integration test loads `examples/plugin_demo/` through entry points
- **THEN** `discover` yields expected items and the example source is at most 60
  lines

### Requirement: FR-018 bounded ingest concurrency
The system SHALL run LLM ingest calls on a bounded worker pool of size
`llm.max_concurrency` (default 4) with retry and backoff. SQLite writes SHALL
remain serialised on the writer thread.

#### Scenario: Injected 429 and 500 complete under the cap
- **WHEN** ingest runs against a local server that returns 429 then 500 then
  success, with concurrency instrumented
- **THEN** ingest completes and observed in-flight LLM calls never exceed
  `llm.max_concurrency`

### Requirement: NFR-006 crash-safe ingest
Ingest SHALL be transactional per record so a process kill mid-sync never
leaves a non-tombstoned record without its FTS row. Pending derived data SHALL
be completed on the next sync. `doctor --deep` SHALL report that consistency.

#### Scenario: SIGKILL injection over 50 iterations
- **WHEN** ingest is SIGKILL'd at random points across 50 iterations
- **THEN** recovered databases have an FTS row for every non-tombstoned record

### Requirement: NFR-008 path jail and secret scrubbing
The files connector SHALL refuse paths outside configured roots, including
symlink and `..` traversal. Logs and reports SHALL not contain secrets. API
keys SHALL come only from the environment.

#### Scenario: Traversal and log grep
- **WHEN** a source path uses `..`, an absolute path, or an escaping symlink
- **THEN** discovery refuses the path and a log grep of a sync with an API key
  in the environment finds no secret values

### Requirement: NFR-009 no shell and read-only MCP
Core SHALL NOT execute a shell. `rg` SHALL be invoked with argument arrays
only. MCP SHALL remain read-only. Prompt-injection hardening from FR-056 SHALL
stay in force. Ruff `S` rules SHALL stay clean.

#### Scenario: Argument-array rg and no shell
- **WHEN** `rg` is used and source is scanned for shell execution
- **THEN** `rg` is invoked as an argument list, no `shell=True` or `os.system`
  appears in core, and ruff `S` is clean

### Requirement: NFR-007 provider degradation
Provider failures SHALL degrade: cards to heuristic, rerank to fused order
with a notice, vec lanes skipped with a notice, and `ask` returning an error
that still includes partial evidence.

#### Scenario: Fault injection across providers
- **WHEN** chat or embedder calls fail during card, rerank, vec, or ask
- **THEN** cards are heuristic, rerank keeps fused order, vec lanes notice a
  skip, and ask returns an error plus retrieved evidence

### Requirement: NFR-015 structured logs
Logs SHALL be JSON when `LODESTONE_LOG=json`, include per-operation timing, use
the cost log, and omit PII and secrets by default.

#### Scenario: JSON logs without PII
- **WHEN** `LODESTONE_LOG=json` and an operation runs
- **THEN** each log line is JSON with `ts`, `level`, `op`, and `duration_ms`
  where timed, and the body contains neither record raw text nor API keys

### Requirement: NFR-004 lexical scale
The engine SHALL support 200,000 lexical-only records with database size at
most 2 GB and documented search RSS at most 500 MB, recorded from a real run.

#### Scenario: Measured 200k-record run
- **WHEN** a 200,000-record lexical-only corpus is indexed and searched
- **THEN** `docs/benchmarks/scale.md` records hardware, DB size, search RSS,
  and latency from that machine

### Requirement: NFR-010 offline privacy data flow
`--offline` SHALL make zero network connections. Default config SHALL send only
card-prompt text and rerank snippets to a configured provider. Docs SHALL
include a data-flow table.

#### Scenario: Socket-blocked offline and documented flow
- **WHEN** sockets are patched to raise and commands run `--offline`
- **THEN** they succeed with no network, and docs contain a data-flow table of
  what leaves the machine per command

### Requirement: doctor --deep consistency
`doctor --deep` SHALL check that every non-tombstoned record has an FTS row,
term_stats df matches a recount sample, embedding dims are uniform per model,
and no orphan children exist. Failures SHALL exit 1.

#### Scenario: Deep check catches a missing FTS row
- **WHEN** a non-tombstoned record has no FTS row
- **THEN** `doctor --deep` exits 1 and names the consistency failure
