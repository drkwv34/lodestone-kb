## Why

Lexical search already retrieves cards, raw text and bursts, but optional embeddings, vector backends and vec lanes are still missing, so hybrid retrieval and offline hash demos cannot run. This change adds the embedding-optional path without requiring a paid API.

## What Changes

- Add an `Embedder` protocol with `HashEmbedder` (256-d signed feature hashing, L2-normalised, not semantic) and `OpenAICompatEmbedder` (existing httpx retry policy and `llm_log` rows) (FR-061).
- Store embeddings for card, chunk and burst records as float32 little-endian BLOBs; delete them with their records; treat model/dim mismatch as missing with a notice until reindex (FR-033).
- Search `vec_card` and `vec_chunk` via sqlite-vec when importable, otherwise brute-force cosine; backends agree within 1e-6 on 1,000 vectors; skip the lanes with `result.notices` when embeddings are disabled or unavailable (FR-033).
- `--offline` / `offline=true` swaps to the hash embedder and heuristic cards; any remote embedder or chat provider attempt raises `OfflineError` (FR-062 partial).
- `reindex --lanes vec` rebuilds embeddings from stored text without contacting sources (FR-083 vec). Optional extra `[vec]` (sqlite-vec).

## Capabilities

### New Capabilities
- `vector-lanes`: optional embeddings, hash and OpenAI-compatible embedders, brute-force and sqlite-vec backends, vec retrieval lanes, offline provider swap, and vec reindex.

### Modified Capabilities

## Impact

New `lodestone.vectors` package; ingest writes embeddings in the derived-data transaction; search and CLI gain vec lanes, notices, `--offline` and `reindex --lanes vec`. Import-linter gains a vectors layer. Existing migrations are not edited. No paid APIs and no network in tests. sqlite-vec tests skip when the extra is absent; CI installs `[vec]` on Ubuntu.
