# Proposal

## Why

`search(explain=True)` currently crashes in the SDK and MCP because fused
packets flatten per-lane explain data into extra keys that `Explain`
(`extra="forbid"`, field `lanes`) rejects. Separately, parent collapse
promotes a thread even when the caller filtered to `kind=burst`, so fused
hits can violate FR-041.

## What Changes

- Emit fused `explain` as the nested `Explain` dump (`lanes`, `rrf`,
  `decay_factor`, `rerank_score`, `final`) and validate the full
  `evidence.v1` packet, including `explain`. Do not relax `extra="forbid"`.
- CLI human and `--json` render from `explain.lanes`. Update
  `schemas/evidence.v1.json` and any tests that assumed the flattened shape.
- When a kind filter is set, collapse uses the best matching member as the
  representative and keeps the parent in parent/children context. Without a
  kind filter, collapse to parent stays (FR-037).
- After fusion, reject any hit that does not satisfy the requested filters
  (FR-041).
- SDK `Lodestone.search(explain=True)` and MCP `search(explain=true)` return
  packets that validate as `Evidence`.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `fusion-search`: nested `explain.lanes` on fused packets (FR-040, FR-042)
  and kind-aware parent collapse so filtered hits stay on matching members
  (FR-037).
- `lexical-search`: fused output with a kind (or other) filter MUST still
  satisfy FR-041 after collapse.
- `rerank-sdk-cli`: `Lodestone.search(explain=True)` validates as
  `evidence.v1` (FR-050).
- `mcp-ask`: MCP `search(explain=true)` returns valid `evidence.v1` hits
  (FR-052).

## Impact

`lodestone.fusion.pipeline` packet dump and collapse representative;
`lodestone.fusion.collapse`; CLI explain rendering; `schemas/evidence.v1.json`;
architecture 3.8 wording if it still shows the flattened shape; SDK and MCP
callers that revalidate packets. Existing `--explain` JSON without a nested
`lanes` object is **BREAKING** for any consumer that treated lane names as
top-level explain keys. No schema migration. No coverage or CI gate changes.
