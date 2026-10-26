# Proposal

## Why

Workspace, retrieval, MCP, ask, and bench already run offline, but connector
plugins, bounded ingest concurrency, crash-safe derived data, complete doctor
diagnostics, structured logging, and documented 200k-record lexical scale are
still missing. Hardening closes those operations and security gaps without
rewriting shipped modules.

## What Changes

- Add an entry-point connector loader (`lodestone.connectors`) plus a
  documented `examples/plugin_demo/` plugin of at most 60 lines.
- Bound LLM ingest calls with `llm.max_concurrency` (default 4) and keep
  retry/backoff; SQLite writes stay on the writer thread.
- Complete `doctor` (sqlite-vec probe, provider reachability when configured
  and not offline, config problems) and add `doctor --deep` consistency checks.
- Complete `reindex --lanes fts|vec|cards` from stored text without contacting
  sources.
- Complete `--offline` so ingest, search, and offline bench strategies succeed
  with sockets patched; remote providers still raise `OfflineError`.
- Add structured JSON logs when `LODESTONE_LOG=json`, per-operation timing, and
  secret/PII scrubbing.
- Add a SIGKILL crash-injection harness (50 iterations) and security tests
  (path jail, log scrubbing, no shell, `rg` argument arrays, ruff `S`).
- Document a measured 200k-record lexical-only scale run in
  `docs/benchmarks/scale.md` and a data-flow table for privacy.
- Extend import-linter if new packages are added. Coverage gate stays 85%.

## Capabilities

### New Capabilities

- `hardening`: plugin connectors, bounded ingest concurrency, crash-safe
  per-record ingest, `doctor --deep`, structured logging, path-jail and log
  scrubbing, provider fault degradation, lexical scale evidence, and privacy
  data-flow documentation.

### Modified Capabilities

- `workspace-foundation`: complete FR-080 diagnostics (sqlite-vec, provider
  reachability when configured and not offline).
- `vector-lanes`: complete FR-062 (offline ingest+search+bench) and FR-083
  (`reindex --lanes fts|vec|cards`).

## Impact

New `lodestone.connectors.plugins`, ingest concurrency helpers, observability
module, doctor/reindex orchestration, `examples/plugin_demo/`, security and
crash tests, `docs/benchmarks/scale.md`, and a privacy data-flow table. CLI
gains `doctor --deep` and full reindex lanes. Storage migrations are not
edited. Tests stay offline with no paid APIs.
