# Benchmark

`lodestone bench` compares retrieval strategies on a corpus you control.
Offline FakeLLM and the hash embedder run in CI. The hash embedder is
deterministic and **not semantic**; reports include that caveat automatically
when it is used.

## Commands

```sh
lodestone bench synth --seed 42 --threads 60 --out ./bench/synth
lodestone bench run --corpus ./bench/synth --out ./bench/run
lodestone bench report ./bench/run
lodestone bench advise ./bench/run
```

Import a local BEIR-format dataset (no download):

```sh
lodestone bench import beir:scifact --from ./beir/scifact --out ./bench/scifact
```

`--from` is a directory or zip with `corpus.jsonl`, `queries.jsonl`, and
`qrels/*.tsv`. Gold ids become files-connector paths (`docs/<id>.md`).
Omitting `--from` downloads the public SciFact zip and checks MD5
`5f7d1de60b170fc8027bb7898e2efca1`. That download is not part of CI.

`synth` writes a deterministic corpus plus `evalset.v1` JSONL. Same seed
produces byte-identical output. `generate` samples questions from an existing
workspace and drops questions whose token overlap with the gold record exceeds
`leakage_max` (default 0.5).

`run` validates the evalset, executes strategies, and writes `report.md` plus
`report.json`. Interrupted runs resume from a cache keyed by strategy, config
hash, corpus hash, and qid (zero duplicate LLM calls).

## Strategies

`classic-rag`, `bm25-chunks`, `hybrid-chunks`, `lodestone-lexical`,
`lodestone-hybrid`, `lodestone-rerank`, `agentic-ask`, `grep-agent`,
`full-context`. `--strategies all` (default) runs every built-in. Skipped
strategies are listed with a reason (`too_large` for full-context over
budget); they are never silently omitted.

## Advise

`lodestone bench advise` applies deterministic rules R1–R4:

1. Embeddings do not pay for themselves on this corpus
2. Consider context stuffing + caching
3. Distillation helps
4. Hybrid default

Each verdict prints evidence lines that point at report cells.

## Real embedders

Synthetic offline numbers live in [benchmarks/FINDINGS.md](benchmarks/FINDINGS.md).
To run with a real embedder, configure `[embed]` / `[llm]` with
`api_key_env` (never a literal key), drop `--offline`, and store the report
under `docs/benchmarks/` with the config hash. If keys are missing, FINDINGS
records `status: not run - needs keys`. Do not invent numbers.
