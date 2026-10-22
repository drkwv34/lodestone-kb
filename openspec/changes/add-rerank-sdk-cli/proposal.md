## Why

Fused search already returns an explainable candidate pool, but callers still
talk to workspace helpers instead of a typed SDK, there is no optional LLM
rerank stage, and the CLI is missing grep, who-knows, recent, stats, and a
privacy-preserving query log. This change closes that public-interface gap
before MCP and ask.

## What Changes

- Add an optional LLM rerank stage after fusion that scores the candidate pool
  and keeps `rerank_keep` hits; on missing reranker, error, timeout, or
  malformed JSON, return the fused order unchanged and attach a notice (FR-039).
- Add a typed `Lodestone` facade in `lodestone/__init__.py` with `py.typed`
  shipped in the wheel, covering open/sync/search/get/grep/who_knows/recent/
  stats (and a typed `ask` stub); include a README snippet that runs as a
  doctest (FR-050).
- Polish CLI commands `search`, `grep`, `get`, `who-knows`, `recent`, and
  `stats` with consistent help and human/`--json` output; snapshot `--help`
  (FR-051 non-bench, non-MCP, non-ask). Implement `who_knows` and `recent`
  (FR-043, FR-044).
- Write `query_log` rows (hash, project, lanes, latency, result count) and
  store query text only when `log.store_queries=true` (FR-081).
- Document Cerebras, OpenAI, and Ollama provider presets as config examples
  with no extra provider-specific code paths beyond the existing optional
  `response_format` flag (FR-064).
- **Not in this change:** MCP server, `ask` execution, or `bench` commands.

## Capabilities

### New Capabilities
- `rerank-sdk-cli`: optional LLM rerank after fusion, typed SDK facade, CLI
  polish for search/grep/get/who-knows/recent/stats, privacy-preserving query
  log, who-knows/recent retrieval, and documented provider presets.

### Modified Capabilities
- `fusion-search`: fused search may apply the optional rerank stage before
  neighbour expansion and populate `explain.rerank_score` when rerank ran.

## Impact

New `lodestone/rerank.py` and SDK types; `query_log` writes using the existing
schema table (no new migration); CLI commands and README doctest; import-linter
layer includes rerank beside fusion and sdk above workspace. Existing fused
search without `--rerank` keeps current order. No paid APIs and no network in
tests. Coverage stays >= 80%.
