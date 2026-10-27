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

H1–H5 in the SRS need a real embedder and/or a larger labelled corpus. This
hash-embedder plumbing run **does not** support those claims. Status: not
tested (see real-embedder line above).

## Other measured runs

Lexical-only 200k-record scale: [scale.md](scale.md).
