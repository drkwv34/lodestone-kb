## Context

Use the supplied architecture sections 3.1 and 7.1, scoped by the Day 1 delivery
plan. Python >=3.11, pydantic v2, Typer and hatchling. See decision 0001 for the
external-content FTS column correction and transactional version stamping.

## Goals / Non-Goals

Goals: offline, repeatable workspace setup; path-aware TOML errors; transactional
migrations; useful runtime probes; blocking quality and license gates.

Non-goals: indexing, providers, search, MCP, SDK, performance or eval tables.

## Decisions

- Extra keys are forbidden recursively. Validation errors omit input values.
- Resolve database and source paths relative to the configuration file.
- Never resolve environment credentials for setup or configuration display.
- OpenSpec is initialised by the real CLI and validated in CI.
- Database connections enforce foreign keys and WAL. Each numbered migration is
  atomic, stamps its version last, and refuses newer versions before mutation.
- Diagnostics inspect the DB read-only and run a real in-memory FTS5 probe.
- The CI matrix covers Ubuntu 3.11/3.12/3.13, macOS 3.12 and Windows 3.12 smoke.

## Risks / Trade-offs

SQLite FTS5 availability varies by Python distribution; errors give remediation.
Lower-bound dependencies may evolve; CI catches compatibility problems. Full
FR-080 provider/sqlite-vec checks remain for the later diagnostics delivery.

## Migration Plan

New workspaces start at schema 1. Do not downgrade databases. Archive the change
only after a green PR head is merged locally; preserve blocked work as partial.
