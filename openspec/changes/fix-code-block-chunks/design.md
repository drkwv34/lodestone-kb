# Design

## Context

See proposal.md for motivation. `symbols()` already classifies class (level 0),
function/method (level 1), and control-flow blocks (level 2). `outline()`
correctly drops level 2. `chunk()` only adds a block start to the cut set when
an enclosing level-1 symbol is longer than `target_tokens * chars_per_token`.
Default limits (400 tokens × 4 chars) are 1600 characters; `figure.code`'s
`run` method is 287 characters, so default ingest yields three chunks.

Child records use `ext_id` `{path}#code:{seq}`. Adding block children shifts
later sequences. Parent `content_hash` already includes `CHUNKER_VERSION`
(`markdown.VERSION + "/" + code.VERSION`) plus kind and chunk settings
(FR-014). Bumping `code.VERSION` is enough to re-chunk on the next `sync`; a
SQL migration is not required.

## Goals / Non-Goals

**Goals:**

- Default (and tight) chunk settings emit the figure.json five-chunk tree.
- Existing workspaces pick up the new children on the next `sync` via the
  versioned content hash and `derived_state='pending'` rewrite.
- Language goldens without block symbols stay unchanged.

**Non-Goals:**

- Parser completeness (still regex, comments/strings masked).
- A new `reindex --lanes chunks` command. `sync` is the rewrite path; FTS/vec
  reindex still rebuilds from stored rows after that rewrite.
- Changing default `target_tokens`.

## Decisions

1. **Always cut method-enclosed blocks.** Add a cut at every level-2 symbol
   whose enclosing symbol is a method (level 1), not only when that method
   exceeds the target. Class and method starts stay unconditional cuts.
   Alternative: lower the default target — rejected because FR-015's 400-token
   default should stay and the figure is the FR-016 source of truth.

2. **Bump `code.VERSION` to `code-v2`.** `upsert` already treats a hash miss as
   a full parent/child rewrite and sets `derived_state` pending. Alternative:
   schema migration that rewrites children in SQL — rejected; chunk text must
   come from the Python chunker, and FR-014 already keys identity on version.

3. **ADR 0010.** Record the version bump and the coarse-to-fine cut rule so
   operators know why `sync` rewrites code children.

4. **Tests.** New `tests/unit/test_code_chunker.py::test_figure_fixture_matches`
   uses default `Chunks()`. Keep the existing tight-target golden. Add an e2e
   that syncs `processor.py` and compares `get processor.py --json` children
   titles to figure.json.

## Risks / Trade-offs

- [More, smaller code children] → Methods with many `if`/`for` nodes become
  more retrieval hits. Acceptable: FR-016 asks for that tree; `pack()` still
  respects max tokens.
- [Child id churn] → Versioned hash plus atomic child delete/insert. Callers
  that stored `code:N` ext_ids must re-sync.
- [Workspaces that never sync] → Stale 3-chunk trees remain until `sync`.
  Document in the ADR; do not silently mutate on read.

## Migration Plan

1. Ship `code-v2` with the cut-rule fix.
2. Operators run `lodestone sync` (offline is fine). Unchanged markdown is
   skipped; code files re-chunk; cards/embeddings requeue via `derived_state`.
3. Rollback: revert to `code-v1` and sync again (restores previous children
   for files whose source text is unchanged).

## Open Questions

None.
