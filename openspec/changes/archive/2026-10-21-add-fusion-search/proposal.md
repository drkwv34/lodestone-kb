## Why

Lexical and vector lanes already return independent ranked lists, but search still exposes a single lane at a time. Hybrid retrieval needs weighted RRF fusion, recency decay, diversity, neighbour expansion, explainable evidence packets, a guarded grep lane, complete filters, and first performance measurements.

## What Changes

- Add `lodestone.fusion` with weighted RRF (`k=60`), recency decay with a floor, rare-token lane weighting, parent collapse, per-source cap, and neighbour expansion (FR-035, FR-036, FR-037, FR-038).
- Add `lanes/grep.py`: regex/literal search over raw text with a catastrophic-regex guard (pattern length <= 500, nested-quantifier rejection, 2 s time budget) (FR-034).
- Add a search pipeline orchestrator that runs available lanes (FTS, vec when enabled, grep when opted in), fuses them, and returns `evidence.v1` packets (FR-042).
- Complete FR-041 filters: project, source, kind, author, date range (`since`, `until`), and metadata equality, applied before fusion.
- `search --explain` reports per-lane rank, raw score, RRF contribution, decay factor, and final score (FR-040). `--no-decay` restores fused order without recency.
- Add `schemas/evidence.v1.json` and validate fused outputs against it.
- Add `pytest -m perf` measurements for NFR-001, NFR-002, and NFR-003 (excluded from the default run).
- **Not in this change:** LLM rerank (FR-039), SDK facade, `who-knows`/`recent`, MCP, or `ask`.

## Capabilities

### New Capabilities
- `fusion-search`: fused hybrid retrieval (RRF, decay, collapse, expansion, grep lane, evidence packets, explain, complete filters, first perf baselines).

### Modified Capabilities
- `lexical-search`: complete FR-041 so author, date range, metadata equality and project filters apply on every lane before fusion, not only source and kind.

## Impact

New `lodestone.fusion` package; `lanes/grep.py`; shared filter SQL on FTS, vec and grep lanes; workspace/CLI fused search with `--explain`, `--no-decay`, `--regex`, author/date/metadata options; `schemas/evidence.v1.json`; import-linter layer includes fusion beside lanes. Existing migrations are not edited. Default single-lane `--lane` search remains available. No paid APIs and no network in tests.
