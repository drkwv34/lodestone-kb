# Design

## Context

See proposal.md. Fused search (RRF, decay, collapse, expand, evidence packets)
already exists. `query_log` is in migration 0001; schema version stays 3.
Architecture 2.2, 3.9, 4.1, 4.2, ADR-007, and the existing import-linter graph
constrain this work. Existing migrations are immutable. Storage must not import
lanes, fusion, or rerank.

## Goals / Non-Goals

**Goals:**
- Optional LLM rerank after collapse and before neighbour expansion, with
  fused-order fallback.
- Typed `Lodestone` facade and `py.typed` in the wheel.
- CLI commands search/grep/get/who-knows/recent/stats with help snapshots.
- Query log writes that default to storing no query text.
- Documented Cerebras/OpenAI/Ollama TOML presets validated by the config schema.

**Non-Goals:**
- MCP server, `ask` execution, bench commands.
- New SQL migrations or schema bumps.
- Changing coverage, ruff, mypy, or import-linter gates.

## Decisions

1. **Rerank is a module beside fusion.** `lodestone.rerank.LLMReranker` takes
   query plus pool snippets (<=1,200 chars). Prompt asks for JSON
   `[{id, score}]` with "rerank" in the text so FakeLLM rule-based overlap
   scoring applies. Scores clamp to 0-10; missing ids score 0; extra ids are
   ignored. Sort key is `(rerank_score desc, fused_score desc)`. Result of
   `rerank()` is a permutation of the input pool; the pipeline then keeps
   `min(limit, rerank_keep)`. Alternative: rerank only the truncated top-k;
   rejected because FR-039 sends the candidate pool.

2. **Fallback is identical to no-rerank.** No chat client, `OfflineError`,
   `ProviderError`, timeout, non-JSON, or schema failure attaches a notice and
   returns the collapsed fused order sliced to `limit`. Tests compare id lists.

3. **SDK sits between CLI and workspace.** `lodestone/sdk.py` implements
   `Lodestone`; `lodestone/__init__.py` re-exports it. CLI builds `Lodestone`
   for search/grep/get/who-knows/recent/stats/sync. `ask` is typed and raises
   a clear not-implemented error until the later MCP/ask change. Import-linter
   layers: `cli` → `sdk` → `workspace` → `fusion | rerank` → existing graph.

4. **Query log uses a short write connection.** Search stays read-only for
   retrieval; after the result is ready, a writable connection inserts one
   `query_log` row. `qhash` is SHA-256 of the query bytes. `query_text` is SQL
   NULL unless `log.store_queries` is true. Grep/who-knows/recent also log.

5. **who_knows scores authors from matching records.** Run lexical/fused
   retrieval for the topic in project scope. For each hit, credit `author` and
   `authors_json` with `decay_factor * (1 + burst_bonus + reaction_bonus)`.
   Burst kind adds 1; metadata `reactions` > 0 adds 1. Return top 5
   `{author, score, records}`. Alternative: SQL-only GROUP BY; rejected because
   recency and lane matching should reuse retrieval.

6. **recent is `updated_at` then id.** Deterministic `ORDER BY updated_at DESC,
   id DESC` with the same Scope filters as search (project, source, kind,
   author, since, until, metadata).

7. **Provider presets are docs plus schema tests.** `docs/providers.md` holds
   three TOML snippets. Tests extract fenced `toml` blocks and `Config.model_validate`
   them. No new client classes; `json_mode` already maps to `response_format`.

8. **Help snapshots and README doctest.** CLI `--help` for the polished
   commands is compared to `tests/fixtures/help/*.txt`. The README Python
   snippet creates a temporary workspace, opens `Lodestone` offline, and is
   executed via doctest in `test_fr_050_readme_doctest`.

## Risks / Trade-offs

- [CLI module size] → keep commands thin via shared emit/error helpers so
  `cli.py` stays <= 500 lines.
- [Rerank vs FakeLLM overlap parser] → prompt uses `Query:` and `id=` lines
  matching `rerank_by_overlap`.
- [Search read-only vs log writes] → separate RW connection; failures to log
  become a notice, never fail the search.
- [ask on the SDK] → typed method present for FR-050; calling it errors until
  the later change.

## Migration Plan

No schema bump. After upgrade, `search` without rerank is unchanged.
`Lodestone.open` is additive. Rollback: omit `--rerank` and keep using CLI
workspace helpers. Query log rows are additive.
