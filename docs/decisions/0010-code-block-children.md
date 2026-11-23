# 0010. Code block children and chunker version

## Status

Accepted.

## Context

FR-016 requires class/struct → function/method → block children. `symbols()`
already finds control-flow blocks at level 2, but `chunk()` only cut at those
starts when the enclosing method exceeded `target_tokens`. Default limits
(400 tokens × 4 chars) leave typical methods unsplit, so `figure.code` became
three chunks instead of the five in `figure.json`.

Child `ext_id` values are `{path}#code:{seq}`. Changing the tree shifts later
sequences. Parent `content_hash` already includes `CHUNKER_VERSION`.

## Decision

Cut at every block that sits inside a method, even when the method is under
the token target. Keep class and method starts as unconditional cuts. Outlines
still omit block-level symbols.

Bump `code.VERSION` from `code-v1` to `code-v2`. The next `sync` sees a hash
miss, replaces children atomically, and sets `derived_state` pending until
cards and embeddings catch up. No SQL migration: stored raw parent text is
re-chunked by the Python chunker.

## Consequences

- `get processor.py --json` after syncing the figure lists `run > if` and
  `run > for` children under default chunk settings.
- Workspaces that never sync keep the old child tree until they do.
- `reindex --lanes fts|vec|cards` still rebuilds from stored rows; run `sync`
  first so those rows match `code-v2`.
