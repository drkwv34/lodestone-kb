# Design

## Context

See proposal.md. Records, cards, bursts, FTS lanes and the embeddings table already exist (schema 3). `embed.provider` is `none|openai_compat|hash`. Chat uses httpx with retry and `llm_log`. Search opens the database read-only. Architecture 3.7, 3.12, ADR-002 and ADR-009 constrain this work. Existing migrations are immutable.

## Goals / Non-Goals

**Goals:**
- Add `lodestone.vectors` with embedder, hash, openai_compat and backends modules.
- Write embeddings in ingest derived-data transactions; keep search read-only.
- Skip vec lanes with notices instead of failing when embeddings are off or mismatched.
- Offline swap to hash embedder plus heuristic cards; `OfflineError` on remote clients.

**Non-Goals:**
- Fusion, RRF, `--explain` evidence packets, grep lane, SDK facade (later features).
- Full FR-062 bench-offline strategies and complete FR-083 `fts|cards` rebuild.
- New numbered SQL migration unless a schema change is required (the embeddings table already exists).
- Persistent sqlite-vec virtual tables in the workspace file (search must stay read-only).

## Decisions

1. **Hash embedder is always 256-d.** Architecture specifies `HashEmbedder(dim=256)`. Config `embed.dim` applies to `openai_compat` only. Alternative: honour `embed.dim` for hash; rejected because tests and ADR-009 pin 256-d hashing.

2. **Signed feature hashing of tokens and bigrams.** Tokens come from `lodestone.tokenize` (same unicode61 rules as FTS). Features are unigrams plus adjacent bigrams. A stable non-salted digest maps each feature to `(index, sign)`; the vector is L2-normalised. Empty input yields a zero vector. Documented as not semantic.

3. **Embeddings BLOB is source of truth.** Writes go to `embeddings(record_id, kind, model, dim, vec)`. sqlite-vec indexes are created lazily in a temporary connection loaded from those BLOBs per `(model, dim)`, so `search` can stay `mode=ro`. Brute-force reads the same BLOBs with `struct`/`array` (numpy when installed). Alternative: persist `vec0` tables in the workspace DB; rejected because that requires write access during search and a new migration.

4. **Cosine via L2-normalised dot product.** Hash and openai vectors are L2-normalised on write. Brute-force scores are dots. sqlite-vec uses `distance_metric=cosine`; distance is converted to similarity `1 - distance` for parity within 1e-6.

5. **Embed kinds.** `card` embeds `embedding_input` text (`embed.source` card|raw|both; both concatenates). `chunk` embeds `context_prefix + text` for `section`/`code`. `burst` embeds prefix plus burst text. `vec_card` queries `kind=card`; `vec_chunk` queries `kind IN ('chunk','burst')` so burst vectors are searchable.

6. **Derived-data transaction.** After cards (and on unchanged records that still need vectors), embeddings are upserted keyed by `content_hash` plus current `(model, dim)`. Record upsert already deletes embeddings for replaced parents; CASCADE covers children. Model/dim mismatch leaves old rows in place but lanes treat them as missing until `reindex --lanes vec`.

7. **OfflineGuard.** `--offline` and `Config.offline` set a runtime guard: chat becomes heuristic (`make_chat` returns `None` except local FakeLLM), and the embedder always becomes `HashEmbedder` so ingest and search can demo vectors with no network even when `embed.provider` is `none`. Constructing or calling `OpenAIChat` / `OpenAICompatEmbedder` while the guard is on raises `OfflineError` before httpx I/O.

8. **Import graph.** `lodestone.vectors` sits with distill: `ingest | lanes` → `distill | vectors` → `providers | storage | ...`. Vectors may import providers (retry constants, `OfflineError`) and storage helpers for packing; storage must not import vectors or lanes.

9. **SearchResult notices.** Single-lane search gains `notices: list[str]` alongside hits. JSON includes `notices`. Disabled/unavailable/mismatch messages name the lane and the remedy (`reindex --lanes vec` when mismatched).

## Risks / Trade-offs

- [sqlite-vec absent] → brute-force backend; tests skip sqlite-vec cases; CI installs `[vec]` on Ubuntu.
- [Hash embedder mistaken for semantic search] → module docstring and notices state it is not semantic (ADR-009).
- [1,000-vector brute force in CI] → acceptable at 256-d; parity test is correctness, not a latency gate.
- [Read-only search rebuilds a temp sqlite-vec index per query] → fine for current corpus sizes; persistent vec tables can wait until a write-path feature owns them.

## Migration Plan

No schema bump unless a gap appears. Existing DBs already have `embeddings`. After upgrade, `sync` or `reindex --lanes vec` fills rows. Rollback is unused-table safe: lexical lanes ignore embeddings.
