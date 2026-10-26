# Design

## Context

See proposal.md. Built-in `files` and `threads` connectors, sequential ingest,
partial `doctor`, vec-only reindex, and a partial offline guard already exist.
FTS is an external-content table kept in the same SQLite transaction as
`records` inserts. `workspace.py` is at the 500-line module cap. Existing
migrations are immutable. Tests must stay offline.

## Goals / Non-Goals

**Goals:**
- Load third-party connectors through entry points without changing the RawItem
  waist.
- Bound LLM ingest concurrency while keeping SQLite writes on one writer.
- Leave lexical rows + FTS committed before derived cards/embeddings so a
  crash is recoverable via `derived_state=pending`.
- Complete doctor, reindex lanes, offline+bench, logging, and security tests
  by extending existing modules.

**Non-Goals:**
- New SQL migrations or schema version bumps.
- Rewriting files/threads connectors, fusion, MCP, or bench strategies.
- Live `rg` as a required runtime; Python grep remains the default.
- Inventing scale numbers; only measured hardware results.

## Decisions

1. **Plugin kind is the entry-point name.** `Source.kind` stays a string:
   `files` and `threads` are builtins; any other kind loads
   `importlib.metadata.entry_points(group="lodestone.connectors")`. Config
   still rejects empty/non-string kinds. Alternative: a separate `plugin`
   field; rejected because FR-017 uses kind as the connector name.

2. **LLM work off-thread, SQLite on the writer.** `ThreadPoolExecutor` of size
   `llm.max_concurrency` runs card LLM calls. Heuristic fallback and all
   writes stay on the main connection. Alternative: `check_same_thread=False`;
   rejected because architecture requires a single writer.

3. **Two transactions per parent.** Transaction 1: parent + children/bursts +
   FTS/term_stats (`derived_state=pending`). Transaction 2: cards + embeddings
   (`ok`/`failed`). Unchanged content with `pending` is completed on the next
   sync. Alternative: one txn including LLM; rejected because a kill would
   roll back searchable text.

4. **Crash harness is a subprocess + `LODESTONE_CRASH_AFTER`.** A child ingest
   decrements that counter after each parent commit and SIGKILLs at zero.
   Fifty iterations are marked `slow`; a short default test runs a few
   iterations in CI. Alternative: in-process raise; rejected because it cannot
   prove WAL recovery.

5. **Doctor and reindex live outside `workspace.py`.** New `lodestone.ops`
   (workspace layer) orchestrates probes, `--deep` checks, and
   `reindex --lanes fts|vec|cards`. Consistency SQL stays in storage.
   Alternative: grow `cli.py`/`workspace.py`; rejected by the 500-line gate.

6. **Optional `rg` uses argv only.** If `rg` is on PATH, grep may spawn
   `["rg", ...]` with no shell. Tests monkeypatch `subprocess.run` to assert
   the argv shape. Python scan remains the default so CI does not require
   ripgrep.

7. **Scale run is a bulk lexical insert, not full ingest.** A documented script
   inserts 200k small records into the real schema, rebuilds FTS, searches,
   and records RSS/DB size. Full per-file ingest at 200k is out of scope for
   this measurement.

## Risks / Trade-offs

- [Plugin kinds weaken the old `kind="invalid"` config fixture] → keep
  non-string/empty kinds invalid so FR-002 still reports `sources[0].kind`.
- [50 SIGKILL iterations are slow or skip on Windows] → mark `slow`; default
  matrix runs a short subset; Windows smoke stays unchanged.
- [200k insert time] → batched transactions; record actual duration; do not
  fabricate results if the run is truncated.
- [JSON logging extra fields] → custom LogRecord factory so `op`/`duration_ms`
 /`ids` are first-class and scrubbed.

## Migration Plan

No schema migration. Existing workspaces keep working. `reindex --lanes fts`
or `cards` is opt-in. Rollback is reverting the feature branch.

## Open Questions

None. Crash-test iteration count and scale hardware are specified; results are
measured at apply time.
