# Design

## Context

See proposal.md. Fusion, lanes, heuristic cards, hash embedder, brute-force
vector search, and workspace ingest already exist. There is no `lodestone.bench`
package, no `evalset.v1` / `report.v1` schemas, and no `window.py`. `cli.py` is
near the 500-line gate. Import-linter currently ends `sdk → workspace | ask`.
Existing migrations are immutable. Tests must stay offline.

## Goals / Non-Goals

**Goals:**
- Isolated per-strategy SQLite indexes from one synth corpus.
- Parent-collapse on `ext_id` so chunk windows and Lodestone cards share gold.
- Report skeleton that is byte-stable except the header timestamp.
- CLI `bench synth|run|report` without crossing the module-size gate.

**Non-Goals:**
- Bootstrap CIs, advise, resume cache, real-corpus questions, answer judge.
- Implementing lodestone-hybrid, lodestone-rerank, agentic-ask, grep-agent, or
  full-context (report them skipped).
- Rewriting storage, lanes, fusion, providers, MCP, or ask.

## Decisions

1. **Bench sits beside SDK, above workspace.** Import-linter:
   `cli → mcp_server → sdk | bench → workspace | ask → …`. CLI imports
   `lodestone.bench.cli`. Bench may import workspace, fusion, ingest, chunking,
   vectors, and storage; nothing below imports bench. Alternative: put bench
   under workspace; rejected because isolation wants a dedicated package and
   architecture 3.13 says bench may import retrieval/ingest, not vice versa.

2. **Isolated strategy databases.** Each strategy builds `strategy_<name>.db`
   under the run directory from the same corpus files. Chunk strategies use
   window text in a private FTS/embedding schema. `lodestone-lexical` inits a
   temp workspace, syncs files+threads offline (heuristic cards, FTS lanes
   only, no vec), and retrieves via fused lexical search. Gold ids are parent
   `ext_id` values (`docs/…`, `code/…`, thread_id). Alternative: reuse one
   Lodestone DB for all strategies; rejected because architecture forbids
   advantaging baselines with Lodestone tables.

3. **Window chunker uses `tokenize()`.** `chunking/window.py` emits 512-token
   windows with overlap 64 using the unicode61 tokenizer, returning `Chunk`
   rows whose text is the original span covering those tokens. Classic-rag
   embeds windows with `HashEmbedder` and brute-force cosine. bm25-chunks
   queries FTS5 BM25. hybrid-chunks fuses both with existing `rrf(k=60)` then
   parent-collapses. Alternative: character windows via `chars_per_token`;
   rejected because FR-073 specifies token windows.

4. **Parent collapse before metrics.** `collapse_parents(ids, parent_of)`
   keeps first-seen parent `ext_id`. Chunk window ids map through
   `parent_ext_id`. Lodestone hits already collapse to parent records inside
   fusion; retrieve still maps `ext_id`. Metrics then compare to `gold_ids`.

5. **Synth is a pure writer.** Seeded `random.Random`, POSIX relative paths,
   LF bytes, JSON objects with a fixed key order, and file `utime` from
   planted ISO timestamps so Lodestone decay sees stale vs fresh. Output
   layout: `threads.jsonl`, `docs/`, `code/`, `evalset.jsonl`. Corpus hash is
   SHA-256 over sorted relative paths and file bytes. Pinned in tests.

6. **Skipped strategies stay in the catalog.** Registry includes
   lodestone-hybrid, lodestone-rerank, agentic-ask, grep-agent, and
   full-context as skipped stubs (`reason: not implemented in this change`).
   `--strategies all` runs in-scope four and records the rest as skipped.

7. **Report skeleton, not statistics.** `report.v1` JSON plus markdown. Header
   may contain `generated_at`; body tables are sorted by strategy name then
   category. Caveats inspect the run config: hash embedder → mandatory
   "hash embedder is not semantic". Leakage stats are a zero/empty placeholder
   (FR-072 is the next change). Cost uses `Prices` (`tokens * price / 1e6`);
   offline hash/FakeLLM retrieval is zero USD when prices are zero.

8. **CLI lives in `lodestone.bench.cli`.** Typer sub-app registered with
   `app.add_typer` so `cli.py` stays under 500 lines. Exit codes match the
   existing 0/1/2 mapping. `run` validates the evalset (FR-070 validation
   command). Default k=20 so recall@20 is defined.

## Risks / Trade-offs

- [Hash embedder is not semantic] → report caveat; tests assert machinery
  (run, collapse, determinism), not paraphrase quality.
- [File mtimes vs content hash] → hash file bytes only; still set utime from
  planted timestamps so decay ranking is reproducible on a given OS.
- [60-thread strategy test runtime] → heuristic cards and hash vectors only;
  no LLM. Keep modules split so window/metrics stay unit-tested without ingest.
- [cli.py line budget] → bench commands in `bench/cli.py`.
- [Coverage vs new package] → FR-named tests covering evalset, synth hash,
  metric goldens, window overlap, parent collapse, four strategies, report
  caveat, and CLI.

## Migration Plan

No schema bump. After upgrade, existing search/MCP/ask behaviour is unchanged.
`lodestone bench` is additive. Rollback: do not run bench commands.
