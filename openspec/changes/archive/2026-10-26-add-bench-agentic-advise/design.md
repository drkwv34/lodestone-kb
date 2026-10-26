# Design

## Context

See proposal.md. `lodestone.bench` already has evalset/synth/metrics/runner,
four baseline strategies, skipped stubs for the remaining five, and a report
skeleton with empty leakage. Fusion, vec lanes, LLM rerank, the ask pipeline,
FakeLLM, and the hash embedder already exist. Tests must stay offline.

## Goals / Non-Goals

**Goals:**
- Replace skipped stubs with isolated implementations of the five remaining
  strategies.
- Generate questions from a real workspace with a leakage filter.
- Attach correctness, optional judge, bootstrap CIs, and paired diffs to the
  existing report without rewriting Bench I metrics.
- Deterministic advise R1–R4 over crafted or real reports.
- JSONL resume cache so retried qids do not call the LLM again.

**Non-Goals:**
- BEIR/SciFact (FR-079).
- Rewriting storage, lanes, fusion, providers, MCP, or ask.
- Claiming semantic quality from hash-embedder runs.
- Changing the 85% coverage gate or CI matrix.

## Decisions

1. **Lodestone hybrid and rerank extend the lexical workspace strategy.**
   `LodestoneLexical` becomes a parameterized workspace strategy: hybrid adds
   `vec_card`/`vec_chunk` and `embed.provider=hash`; rerank uses the same index
   plus `search_result(..., rerank=True, provider="fake")` so FakeLLM scores
   the fused pool. Alternative: separate ingest pipelines; rejected because
   isolation already uses one temp workspace per strategy and ingest already
   writes hash vectors when offline.

2. **agentic-ask retrieval is cited evidence, not fused hits.** Index like
   hybrid. `retrieve` runs `run_ask` with FakeLLM, maps citation labels to
   record `ext_id` (parent-collapsed), and `answer` returns the synthesised
   text from that same call so the LLM is not invoked twice per qid.
   Alternative: treat fused search as retrieval; rejected because FR-073 says
   retrieval is the union of cited evidence.

3. **grep-agent stays on raw files.** Index walks `docs/`, `code/`, and
   `threads.jsonl` into `{ext_id, text}` rows. The loop allows only `grep` and
   `read`, max 8 tool calls. Unparseable FakeLLM output falls back to
   identifier/token grep of the question. Alternative: reuse `lanes.grep` on a
   Lodestone DB; rejected because architecture says raw files only.

4. **full-context skip is `too_large`.** Concatenate corpus text, count tokens
   with `tokenize()`. If count > `context_budget_tokens` (default 128000),
   set `skipped="too_large"`. Otherwise `answer` stuffs the corpus into one
   FakeLLM prompt. `retrieve` returns all parent `ext_id`s (capped at k) when
   feasible so recall is defined.

5. **Correctness is `must_contain`; judge is optional.** Substring match over
   `gold_answer_must_contain` (case-insensitive). Empty needles score 1.0.
   `--judge` asks FakeLLM for a 0–1 score and records it beside substring
   correctness. Retrieval-only strategies without `answer()` get correctness
   null unless they implement `answer`.

6. **Percentile bootstrap, no numpy dependency.** `random.Random(seed)` with
   2,000 resamples of the per-question metric vector; CI is the 2.5th and
   97.5th percentile of resampled means. Paired diffs subtract per-qid scores
   vs `classic-rag`. Seed from the run config hash so reports are reproducible.
   Alternative: BCa bootstrap; rejected as unnecessary for the SRS.

7. **Advise evaluates R1 then R2 then R3, else R4.** First matching rule is
   the verdict; every evaluated rule still emits evidence lines. Embedding
   strategies: `classic-rag`, `hybrid-chunks`, `lodestone-hybrid`,
   `lodestone-rerank`. Cards strategy for R3: `lodestone-lexical`. Crafted
   reports in unit tests supply the cells; advise does not re-run retrieval.

8. **Resume cache is JSONL in the run directory.** Key
   `(strategy, config_hash, corpus_hash, qid)`. Values store retrieved ids,
   answer, tokens, latency. The runner skips `retrieve`/`answer` on hit.
   Indexing still runs (heuristic cards / hash embed; no chat). Alternative:
   SQLite `eval_results`; rejected to avoid a schema bump for a temp run dir.

9. **CLI stays in `bench/cli.py`.** Add `generate` (`--corpus` lodestone.toml,
   `--n`, `--out`, `--leakage-max`) and `advise` (run directory). `run` gains
   `--judge`, `--reps`, `--context-budget`, and always writes/reads the cache
   file. `cli.py` stays under the 500-line gate.

## Risks / Trade-offs

- [Hash embedder is not semantic] → keep FR-076 caveat; tests assert
  machinery (leakage, skip reason, cache hits, rule firing), not paraphrase
  quality.
- [Nine strategies on threads=60 may exceed the 5-minute offline target] →
  keep the existing 60-thread test on the four baselines; remaining
  strategies use a small synth corpus in CI; evidence transcript uses a small
  corpus timed locally.
- [FakeLLM tool JSON may not match grep-agent] → heuristic grep fallback so
  retrieve still returns ids offline.
- [Advise on sparse reports] → missing cells fail the matching rule and fall
  through; R4 always applies.
- [Resume after config change] → different config hash misses the cache, so
  tokens are spent again (correct).

## Migration Plan

No schema bump. Existing `lodestone bench synth|run|report` keep working.
Rollback: do not invoke `generate` or `advise`; skipped stubs are gone, so
`--strategies all` now runs the five new strategies instead of stubbing them.
