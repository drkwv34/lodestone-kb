# Concepts

Lodestone is a local knowledge engine. Every source becomes records of one
shape. Every retrieval path is a *lane* that returns ranked record ids.
Fusion, expansion and rerank do not know where a hit came from.

## Records and cards

A files source yields a parent `doc` or `code_file` plus ordered `section` or
`code` children. A threads JSONL source yields a `thread` parent and, when
the burst gate fires, `burst` children. Each record keeps raw text.

A *card* is a question-shaped summary (`question`, `summary`, `resolution`,
entities, code refs) used as a retrieval view. `--offline` and missing or
failing chat providers fall back to a heuristic card. Raw text is always
retained for FTS and citations.

## Lanes and fusion

Default search fuses:

- `fts_raw` — BM25 over raw title/text
- `fts_card` — BM25 over card text
- `fts_rare` — rare-token lane
- optional `vec_card` / `vec_chunk` when embeddings exist
- optional `grep` when requested

Ranks are combined with weighted RRF (`k=60`), then recency decay, parent
dedupe and a per-source cap. `--explain` shows lane contributions.
`--lane NAME` runs a single lane. Embeddings stay off until
`embed.provider` is `hash` or `openai_compat`, or until `--offline` swaps in
the hash embedder.

## Projects and sources

`lodestone.toml` lists named sources and projects. `source add` registers a
source and includes it in the selected project (`workspace.default_project`
if omitted). Search, sync and source commands accept `--project`. Repeatable
`--source` filters intersect project membership.

## Offline vs providers

`--offline` / `offline = true` replaces remote chat with `FakeLLM` or
heuristic cards and remote embeddings with the hash embedder. Optional
providers are OpenAI-compatible HTTP only (`base_url`, `model`,
`api_key_env`). Presets: [providers.md](providers.md).

## Ask and MCP

`lodestone ask` plans tool calls (`search`, `grep`, `who_knows`, `recent`),
gathers evidence, and synthesises an answer with `[n]` citations. The MCP
server exposes the same retrieval tools over stdio with the database opened
read-only. Details: [mcp.md](mcp.md).
