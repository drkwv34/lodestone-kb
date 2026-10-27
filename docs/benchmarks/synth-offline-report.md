# Lodestone bench report
Generated: 2026-10-27T16:16:53+00:00

## Run
- config_hash: 0370c0c69e97d15f6427d70118f6fb12fa4246fd0ff66bf2e516de51090fd784
- corpus_hash: 8db83e28f409b7a6801f74d91e4d7c1a7a8911ad977cee05ead2a4fe6be0bf79
- lodestone: 0.1.0.dev0
- embedder: hash

## Strategies
| strategy | status | recall@1 | recall@5 | recall@10 | recall@20 | mrr | ndcg@10 | index_s | index_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25-chunks | ok | 0.225000 | 0.700000 | 0.850000 | 0.850000 | 0.356726 | 0.440418 | 0.042310 | 98304 |
| lodestone-lexical | ok | 0.475000 | 0.775000 | 0.775000 | 0.775000 | 0.529167 | 0.514692 | 0.231122 | 446464 |
| classic-rag | ok | 0.225000 | 0.500000 | 0.550000 | 0.550000 | 0.258333 | 0.293996 | 0.050198 | 102400 |
| hybrid-chunks | ok | 0.225000 | 0.650000 | 0.900000 | 0.900000 | 0.330754 | 0.429502 | 0.053341 | 163840 |

## Per category
| strategy | category | recall@10 | mrr | ndcg@10 |
| --- | --- | --- | --- | --- |
| bm25-chunks | exact_token | 1.000000 | 0.500000 | 0.630930 |
| bm25-chunks | paraphrase | 1.000000 | 0.158631 | 0.347965 |
| bm25-chunks | stale_vs_fresh | 1.000000 | 0.500000 | 0.630930 |
| bm25-chunks | tangent_in_long_thread | 0.000000 | 0.000000 | 0.000000 |
| bm25-chunks | multi_source | 1.000000 | 1.000000 | 1.000000 |
| bm25-chunks | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| lodestone-lexical | exact_token | 1.000000 | 1.000000 | 1.000000 |
| lodestone-lexical | paraphrase | 1.000000 | 0.520833 | 0.640402 |
| lodestone-lexical | stale_vs_fresh | 1.000000 | 0.500000 | 0.630930 |
| lodestone-lexical | tangent_in_long_thread | 0.000000 | 0.000000 | 0.000000 |
| lodestone-lexical | multi_source | 0.500000 | 1.000000 | 0.613147 |
| lodestone-lexical | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| classic-rag | exact_token | 1.000000 | 0.500000 | 0.630930 |
| classic-rag | paraphrase | 0.000000 | 0.000000 | 0.000000 |
| classic-rag | stale_vs_fresh | 0.333333 | 0.055556 | 0.118736 |
| classic-rag | tangent_in_long_thread | 0.000000 | 0.000000 | 0.000000 |
| classic-rag | multi_source | 1.000000 | 1.000000 | 1.000000 |
| classic-rag | unanswerable | 1.000000 | 0.000000 | 0.000000 |
| hybrid-chunks | exact_token | 1.000000 | 0.500000 | 0.630930 |
| hybrid-chunks | paraphrase | 0.500000 | 0.066964 | 0.162200 |
| hybrid-chunks | stale_vs_fresh | 1.000000 | 0.333333 | 0.500000 |
| hybrid-chunks | tangent_in_long_thread | 1.000000 | 0.115741 | 0.305842 |
| hybrid-chunks | multi_source | 1.000000 | 1.000000 | 1.000000 |
| hybrid-chunks | unanswerable | 1.000000 | 0.000000 | 0.000000 |

## Cost and latency
| strategy | in_tokens | out_tokens | usd | p50_ms | p95_ms | p99_ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25-chunks | 2643 | 0 | 0.000000 | 2.180105 | 2.807002 | 2.809776 |
| lodestone-lexical | 0 | 0 | 0.000000 | 11.082024 | 13.328129 | 14.120980 |
| classic-rag | 2643 | 0 | 0.000000 | 0.428996 | 0.538631 | 0.840868 |
| hybrid-chunks | 2643 | 0 | 0.000000 | 2.648936 | 3.290819 | 3.364186 |

## Leakage
- dropped: 0
- histogram: none

## Caveats
- hash embedder is not semantic
- leakage stats are a placeholder until real-corpus question generation

## Failures
- none
