# Benchmark findings

Numbers below are from one synthetic offline run on this machine. The hash
embedder is **not semantic**. Do not treat these scores as evidence about
embedding quality.

Real-embedder run: `status: not run - needs keys`

## Hardware (synthetic run)

- Host: Linux 6.12.94+ x86_64 (`uname -a`: `Linux cursor 6.12.94+ #1 SMP PREEMPT_DYNAMIC Mon Oct 26 18:36:23 UTC 2026 x86_64`)
- CPU: 4 logical CPUs (`nproc` = 4)
- Python: 3.12.3
- SQLite: 3.45.1
- lodestone-kb: 0.1.0.dev0

## Synthetic offline command

```text
$ lodestone bench synth --seed 42 --threads 20 --out /tmp/lodestone-docs-bench/synth
wrote 20 questions to /tmp/lodestone-docs-bench/synth/evalset.jsonl
corpus_hash 8db83e28f409b7a6801f74d91e4d7c1a7a8911ad977cee05ead2a4fe6be0bf79

$ lodestone bench run --corpus /tmp/lodestone-docs-bench/synth --out /tmp/lodestone-docs-bench/run \
    --strategies "bm25-chunks,lodestone-lexical,classic-rag,hybrid-chunks" --k 10
wrote /tmp/lodestone-docs-bench/run/report.md

$ lodestone bench advise /tmp/lodestone-docs-bench/run
verdict: distillation helps
rule: R3
evidence:
- lodestone-lexical paraphrase recall@10=1.0000 > classic-rag=0.0000 significant
```

Verbatim report: [synth-offline-report.md](synth-offline-report.md).
Advise output: [synth-offline-advise.md](synth-offline-advise.md).

config_hash: `0370c0c69e97d15f6427d70118f6fb12fa4246fd0ff66bf2e516de51090fd784`

## How to run with a real embedder

1. Set `CEREBRAS_API_KEY`, `OPENAI_API_KEY`, or an Ollama endpoint. Keys stay
   in the environment (`api_key_env`); never paste them into TOML.
2. Copy a preset from [../providers.md](../providers.md) into `lodestone.toml`.
3. Generate or reuse an evalset, then:

```sh
lodestone bench run --corpus ./bench/synth --out ./bench/real
```

4. Commit `report.md` / `report.json` under `docs/benchmarks/` with the config
   hash in the filename. Replace this file's real-embedder line with measured
   numbers. Never invent scores.

Until those keys exist: `status: not run - needs keys`.

## Hypotheses H1–H5

Statuses use only numbers from the committed synthetic run above
([synth-offline-report.md](synth-offline-report.md),
[synth-offline-advise.md](synth-offline-advise.md)) and [scale.md](scale.md).
The hash embedder is not semantic, so these rows cannot support embedding
quality claims. Real-embedder run: `status: not run - needs keys`.

| ID | Hypothesis | Status | Evidence |
|---|---|---|---|
| H1 | On `paraphrase` and `tangent_in_long_thread`, `lodestone-hybrid` improves recall@5 over `classic-rag` by >= 10 pp | not tested | Committed run did not include `lodestone-hybrid`. Hash embedder is not semantic. |
| H2 | On `exact_token`, `lodestone-lexical` is within 3 pp of `lodestone-hybrid` | not tested | Committed run did not include `lodestone-hybrid`. `lodestone-lexical` exact_token recall@10 = 1.000000 in [synth-offline-report.md](synth-offline-report.md). |
| H3 | On `stale_vs_fresh`, decay raises the correct (fresh) answer rank over `--no-decay` in >= 80% of paired cases | not tested | Committed run did not compare decay vs `--no-decay`. |
| H4 | Cards cost X tokens/record at ingest; report break-even vs per-query savings | not tested | Committed run used heuristic cards (`lodestone-lexical` in_tokens = 0, usd = 0.000000). No LLM card-cost series. |
| H5 | `full-context` wins accuracy when corpus <= budget but costs >= 5x per query | not tested | Committed run did not include `full-context`. |

Related (not H1–H5): `lodestone bench advise` on this hash-embedder run said
`distillation helps` (R3) because lodestone-lexical paraphrase recall@10 =
1.0000 > classic-rag = 0.0000. That is lexical overlap on a synthetic
corpus, not a semantic embedding result.

## Other measured runs

Lexical-only 200k-record scale: [scale.md](scale.md).
