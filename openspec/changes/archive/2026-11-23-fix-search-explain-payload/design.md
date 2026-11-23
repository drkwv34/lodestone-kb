# Design

## Context

See proposal.md. Fusion already builds a Pydantic `Explain` with field
`lanes`, then overwrites the dumped packet with flattened lane keys and
skips `explain` during `validate_packet`. SDK `Evidence.model_validate` and
MCP `_dump_hit` then reject those keys because `Explain` uses
`extra="forbid"`. Collapse always sets the representative to `parent_id`
when present, so a kind filter that matched only bursts still lists the
thread. Architecture 3.8 currently writes the flattened shape; the `Explain`
model is nested. ADR 0009 records the nested-lanes contract.

## Goals / Non-Goals

**Goals:**
- One packet dump path: `explain_obj.model_dump()` (or equivalent nested
  dump) plus full-packet validation.
- Kind-aware collapse representative; post-check that every emitted hit
  satisfies `Scope`.
- CLI human/`--json` read `explain.lanes`.
- Tighten `schemas/evidence.v1.json` explain object without relaxing
  `extra="forbid"`.

**Non-Goals:**
- New retrieval lanes, schema migrations, coverage or CI gate changes.
- Changing unfiltered parent collapse (FR-037 without a kind filter).
- Ask-pipeline planner or ingest work.

## Decisions

1. **Nested explain is the packet contract.** Pipeline assigns
   `payload["explain"] = explain_obj.model_dump()` and calls
   `validate_packet` on the full payload. Alternative: keep flattening and
   relax `Explain.extra`; rejected because callers already model nested
   `lanes` and `extra="forbid"` is the safety net.

2. **JSON schema matches `Explain`.** `explain` becomes an object with
   `lanes`, `rrf`, `decay_factor`, `rerank_score`, `final` and
   `additionalProperties: false`. `validate_packet` keeps its top-level
   check; Pydantic `Evidence` remains the nested validator. Alternative:
   pull in a JSON Schema library; rejected as unnecessary for this fix.

3. **Kind filter selects the member, not the parent.** `collapse(...,
   promote_parent=True)` keeps today's parent representative. When
   `scope.kinds` is set, `promote_parent=False` so `id` is the best member
   (already filter-matching); `parent_id` and sibling `matched_children`
   stay for context; the representative is omitted from packet children.
   Alternative: always emit the parent and rewrite `kind` on the packet;
   rejected because FR-041 requires the hit itself to satisfy the filter.

4. **Post-check after packet build.** Before appending a hit, load the
   representative row and drop it if it fails `Scope` (kind, source,
   author, dates, metadata). This catches any future collapse/promote
   mismatch. Alternative: trust lane SQL only; rejected because collapse
   currently rewrites identity after the lanes.

5. **CLI renders `explain.lanes`.** Human `--explain` and tests that summed
   `explain.values()` switch to `explain["lanes"]`. Top-level `rrf` /
   `decay_factor` / `final` stay where they are.

6. **Architecture 3.8 and ADR 0009.** Update the architecture `explain`
   line to `{lanes: {lane: {rank, raw_score, contribution}}, rrf,
   decay_factor, rerank_score, final}`. Record the flattening bug and
   kind-filter representative in `docs/decisions/0009-explain-nested-lanes.md`.

## Risks / Trade-offs

- [External `--explain --json` consumers that keyed lanes at the explain
  root] → documented **BREAKING** in the proposal; in-repo tests and CLI
  are updated in this change.
- [Kind-filtered results no longer list the thread title as the hit] →
  intended; parent remains in `parent_id` / children context.
- [Post-check silently drops a hit] → preferred over returning a
  filter-violating parent; tests assert burst kind rather than empty
  results on the thread fixture.

## Migration Plan

No SQLite migration. After upgrade, `search(explain=True)` and MCP
`explain: true` succeed. Rollback: prior commits; no data rewrite.

## Open Questions

None.
