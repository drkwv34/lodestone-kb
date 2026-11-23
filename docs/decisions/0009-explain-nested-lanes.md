# 0009. Nested explain lanes and kind-filtered collapse

## Status

Accepted.

## Context

Fusion builds a Pydantic `Explain` model with a `lanes` map. The pipeline then
flattened those lanes into extra keys on the dumped packet and skipped
`explain` during `validate_packet`. SDK `Evidence.model_validate` and MCP
`search(explain=true)` reject extra keys because `Explain` uses
`extra="forbid"`. Architecture 3.8 had been written in the flattened form.

Parent collapse always used `parent_id` as the listed hit. A kind filter of
`burst` therefore returned the parent thread, violating FR-041.

## Decision

Fused packets emit `explain_obj.model_dump()`: `{lanes, rrf, decay_factor,
rerank_score, final}`. The full packet, including `explain`, validates against
`schemas/evidence.v1.json` and `Evidence`. `extra="forbid"` stays.

When a kind filter is set, collapse lists the best matching member and keeps
the parent in parent/children context. Without a kind filter, collapse still
lists the parent (FR-037). After packet build, every hit is checked against
the same `Scope` used by the lanes.

CLI human and `--json` render from `explain.lanes`. Architecture 3.8 matches
the nested object.

## Consequences

`--explain --json` that treated lane names as top-level explain keys is a
breaking shape change. In-repo CLI, SDK, MCP, and tests follow the nested
form. No SQLite migration.
