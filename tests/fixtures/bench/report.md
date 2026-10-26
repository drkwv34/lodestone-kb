# Lodestone bench report
Generated: 2026-01-02T00:00:00+00:00

## Run
- config_hash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
- corpus_hash: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
- lodestone: 0.1.0.dev0
- embedder: hash

## Strategies
| strategy | status | recall@1 | recall@5 | recall@10 | recall@20 | mrr | ndcg@10 | index_s | index_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic-rag | ok | 0.500000 | 1.000000 | 1.000000 | 1.000000 | 0.500000 | 0.693426 | 1.250000 | 4096 |
| lodestone-hybrid | skipped |  |  |  |  |  |  | 0.000000 | 0 |

## Per category
| strategy | category | recall@10 | mrr | ndcg@10 |
| --- | --- | --- | --- | --- |
| classic-rag | exact_token | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | paraphrase | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | stale_vs_fresh | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | tangent_in_long_thread | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | multi_source | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | unanswerable | 1.000000 | 1.000000 | 1.000000 |
| lodestone-hybrid | exact_token |  |  |  |
| lodestone-hybrid | paraphrase |  |  |  |
| lodestone-hybrid | stale_vs_fresh |  |  |  |
| lodestone-hybrid | tangent_in_long_thread |  |  |  |
| lodestone-hybrid | multi_source |  |  |  |
| lodestone-hybrid | unanswerable |  |  |  |

## Cost and latency
| strategy | in_tokens | out_tokens | usd | p50_ms | p95_ms | p99_ms |
| --- | --- | --- | --- | --- | --- | --- |
| classic-rag | 0 | 0 | 0.000000 | 1.000000 | 2.000000 | 3.000000 |
| lodestone-hybrid | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

## Leakage
- dropped: 0
- histogram: none

## Caveats
- hash embedder is not semantic
- lodestone-hybrid skipped: not implemented in this change
- leakage stats are a placeholder until real-corpus question generation

## Failures
- none
