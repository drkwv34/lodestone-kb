# Proposal

## Why

Retrieval, MCP, and ask already exist, but teams still cannot compare classic
RAG, BM25 chunks, hybrid chunks, and Lodestone lexical search on a shared
corpus. This change adds the offline benchmark harness so those four strategies
can be scored with honest retrieval, cost, and latency metrics.

## What Changes

- Add `evalset.v1` JSONL validation (`qid`, `question`, `gold_ids`, optional
  `gold_answer_must_contain`, `category`, optional `source_hint`) with line
  numbers on invalid rows.
- Add `lodestone bench synth --seed N --threads N` that emits a deterministic
  corpus (threads, docs, code) plus evalset covering `exact_token`,
  `paraphrase`, `stale_vs_fresh`, `tangent_in_long_thread`, `multi_source`, and
  `unanswerable`. Same seed yields byte-identical output.
- Add strategy interface `index` / `retrieve` / optional `answer` and four
  offline strategies: `classic-rag`, `bm25-chunks`, `hybrid-chunks`,
  `lodestone-lexical`. Each indexes an isolated SQLite file.
- Add a fixed-window chunker (`window.py`, 512 tokens, overlap 64) used by the
  classic/BM25/hybrid chunk strategies.
- Add retrieval metrics (recall@{1,5,10,20}, MRR, nDCG@10 with parent
  collapse), cost (tokens and USD from the price table), latency percentiles,
  and index build time/bytes.
- Add report skeleton `report.md` / `report.json` (`report.v1`) with config and
  corpus hashes, versions, per-strategy and per-category tables, cost/latency,
  leakage placeholder, caveats (including "hash embedder is not semantic"), and
  failures. Skipped strategies are listed, never silently omitted.
- Add CLI `lodestone bench synth|run|report`.

**Not in this change:** `lodestone-hybrid`, `lodestone-rerank`, `agentic-ask`,
`grep-agent`, `full-context`, real-corpus question generation (FR-072),
bootstrap CIs (FR-075), advise (FR-077), resume cache (FR-078), answer
correctness / LLM-judge.

## Capabilities

### New Capabilities

- `bench-formats-synth`: evalset and report schemas, synthetic corpus
  generator, baseline retrieval strategies, parent-collapsed metrics, report
  skeleton, window chunker, and `lodestone bench synth|run|report`.

### Modified Capabilities

- (none)

## Impact

New `lodestone.bench` package and `lodestone.chunking.window`; CLI `bench`
subcommands; `schemas/evalset.v1.json` and `schemas/report.v1.json`;
import-linter layer for bench above workspace. Storage, lanes, fusion,
providers, MCP, and ask are reused, not rewritten. No paid APIs and no
network in tests. Coverage gate stays 85%.
