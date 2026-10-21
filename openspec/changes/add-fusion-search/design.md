# Design

## Context

See proposal.md. FTS lanes (`fts_raw`, `fts_card`, `fts_rare`), optional `vec_card`/`vec_chunk`, ingest, cards and embeddings already exist. Search today is single-lane. Architecture 2.2, 3.6, 3.8, 4.3, ADR-004 and failure-mode "Catastrophic regex" constrain this work. Existing migrations are immutable. Storage must not import fusion or lanes.

## Goals / Non-Goals

**Goals:**
- Pure fusion helpers (RRF, decay, collapse, expand) plus a pipeline that runs enabled lanes and emits `evidence.v1`.
- Grep lane with a signal-free time budget and a static pathological-pattern guard.
- Complete filters on every lane before fusion.
- Keep `--lane` single-lane search working; default search with no `--lane` runs fusion.
- First NFR-001..003 measurements under `pytest -m perf`.

**Non-Goals:**
- LLM rerank (FR-039), SDK `Lodestone` facade, `who-knows`/`recent`, MCP, `ask`.
- Persistent sqlite-vec tables or a new SQL migration.
- Changing coverage, ruff, mypy or import-linter gates.

## Decisions

1. **Fusion sits beside lanes.** Import-linter layer becomes `ingest | lanes | fusion`. Fusion may import lanes and storage; storage must not import fusion. Workspace calls `fusion.pipeline.search`; CLI stays thin.

2. **RRF then decay then collapse then expand.** Matches architecture 2.2 and ADR-004: lanes have incomparable scores, so rank-based fusion happens first; decay is a multiplicative factor `max(floor, 0.5 ** (age_days / half_life_days))` with `age_days` clamped at 0 for future timestamps. `half_life_days=0` disables decay for that kind. Burst uses thread decay; section uses doc; `code_file` uses code.

3. **Cerebras figure.** Score `sum 1/(60+rank)` for ranks 2, 3, 1, 5, 5 (document absent from the sixth list) equals 0.079165 ≈ 0.0792. Weights default to 1.0 in that unit test; production uses config weights including `fts_rare=0.7` as rare-token weighting.

4. **Collapse then per-source cap.** Group by `parent_id` or self; keep the best-scoring member; attach other group members as `matched_children` / packet `children`. Then fill `candidate_pool` (20) while taking at most `max_per_source` (3) collapsed hits per source. Alternative: cap before collapse; rejected because the spec wants the file listed once with children.

5. **Grep is opt-in.** Config may list `grep`, but the fused pipeline runs it only for `--lane grep` or `--regex`. Scan `records.text` in Python with a 2 s monotonic deadline. Reject `len(pattern) > 500` and nested-quantifier forms such as `(a+)+`. SQLite `REGEXP` is registered for optional SQL use; the lane itself uses the Python scanner so the budget cannot be bypassed. `rg` is unused in tests.

6. **Filters are a shared WHERE builder.** `lanes.scope.Scope` adds parameterised `sources`, `kinds`, `authors` (`author` column or `authors_json`), `since`/`until` on `updated_at`, and `json_extract` metadata equality with identifier-only keys. Empty lists yield no hits. Project scope remains `Config.scoped_sources`.

7. **Evidence packets.** Pydantic `Evidence` matches `schemas/evidence.v1.json`. Tests validate every fused packet against that file. `--explain` fills `explain` with `{lane: {rank, raw_score, contribution}, rrf, decay_factor, rerank_score, final}` where `rerank_score` is null until FR-039. Single-lane JSON shape is unchanged when `--lane` is set.

8. **Perf tests are opt-in.** `pytest.ini` already excludes `perf`. Tests insert or ingest 20,000 synthetic records, print NFR-001 p95 ms, NFR-002 records/s and NFR-003 no-change sync seconds, and record a decision if a target is missed.

## Risks / Trade-offs

- [20k-record perf on CI] → measurements are printed, not a blocking job; if above target, add `docs/decisions/0006-fusion-perf-baseline.md` with a plan.
- [Collapse vs cap wording] → tests cover six chunks collapsing to one parent with children, and a separate per-source cap on distinct parents.
- [Catastrophic regex false positives] → guard is conservative; literal mode `re.escape`s the query.
- [Default search becomes fused] → existing single-lane tests pass `--lane`; workspace callers still get hits for the same tokens because FTS lanes remain in the fusion set.

## Migration Plan

No schema bump. After upgrade, `search` without `--lane` fuses configured FTS lanes (and vec when embeddings exist). Rollback: pass `--lane fts_raw`. Evidence schema is additive.
