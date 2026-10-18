# 00 - Research summary: from the Cerebras knowledge-base post to "Lodestone"

Prepared 2026-10-16 (America/Guayaquil). All GitHub numbers were fetched live from the GitHub REST API on 2026-10-16 ~14:58-15:20 (UTC-5); raw data in `research/gh-stats.tsv` and `research/gh-stats-extra.tsv`.
Statements marked **[assessment]** are my own judgement, not sourced facts.

## 1. What I could and could not read

| Item | Result |
|---|---|
| `x.com/cerebras/status/2077822555159945507` via WebFetch | 403 Forbidden |
| Same post via `api.fxtwitter.com` | OK: tweet is a link card to an **X Article** "How we built our knowledge base" (Cerebras, 2026-07-16 18:27 UTC; authors Isaac Tai, Daniel Kim, Mike Gao). Full article body (108 blocks) and metadata retrieved |
| Blog version `cerebras.ai/blog/how-we-built-our-knowledge-base` (dated Jul 15 2026) | OK via WebFetch; text identical in substance |
| Images | 12 images downloaded to `source/img00..11.jpg` and each viewed. Transcribed below |
| Not accessed | The blog's interactive/animated widgets (only their static labels came through); the linked papers were not all re-read (RRF 2009, HNSW 2016, Search-o1, etc.): they are cited by the post and I rely on the post's description of them |

Nothing in this report is invented about the post. The post has **no quantitative benchmark** (only "accuracy increased significantly" when threads were normalized) and does not release code or the prompts.

## 2. Post digest

**Thesis**: don't centralize data; "meet data where it lives" and build one hybrid retrieval layer. Cerebras Knowledge handles 15,000+ questions/day (3 months after launch), used by humans, automations and agents.

**Architecture (6 layers, figure img00/img04)**: Sources (Slack, wiki, code, incidents) -> Distillation (LLM extractors) -> Embeddings (pgvector, 3072-dim, HNSW) -> Retrieval (six ranked lists in parallel) -> Fusion + rerank (RRF k=60 -> LLM rerank) -> Synthesis (answer + citations).

**Key mechanisms**
1. **One table, one connector per source** (img10): document, embedding, metadata, source+timestamps. Custom sources = a small Python plugin emitting rows in that shape.
2. **Slack ingestion** (img08): Socket Mode event -> ack + dedupe by event id -> route (@mention/DM => bot reply; tracked channel => `reingest_thread` => `upsert thread` -> `sync_worker` => distill, thread vector, burst vectors). Every message triggers re-fetch of the *whole* thread so the row always reflects the full conversation. One data source per channel for freshness tuning.
3. **Distillation** (img01): raw thread -> JSON artifact {question, summary, resolution, systems[], code_refs[]} -> normalized document (question+summary+resolution+systems+code refs) -> 3,072-d row with metadata (channel, authors, time). The raw transcript is not embedded. Also keep Postgres FTS (GIN) over raw text.
4. **Four signals** (img02): full-text (exact tokens, pasted errors), embedding (paraphrase), IDF (rare tokens beat filler like "sounds good, thanks!"), age decay (newer wins ties; an 8-month-old answer is penalized).
5. **Bursts** (img03): runs of same-author messages, embedded with thread topic prepended; embedded only if rare token IDF>=4.0, >=200 chars, or reactions.
6. **Code** (img11): CocoIndex; language-aware recursive regex chunking coarse->fine (class -> method -> if/for), multi-granularity records (file + function), incremental re-embedding on commit, sync state stored in the same Postgres. Config-file onboarding with path allow/deny lists. Repos >40 GB.
7. **Planner -> parallel tool fan-out -> evidence -> synthesis** (img09): tools subsystem_index, search, search_slack, search_code (ripgrep), recent_prs, who_knows; planner sees a compact catalog of indexed projects/sources.
8. **Fusion** (img06): RRF score(d)=sum w/(60+rank); I verified the figure's merged score 0.0792 = 1/62+1/63+1/61+1/65+1/65 (ranks 2,3,1,5,5 across five of the six lists), so it is plain RRF. Then dedupe to source, cap per file, top 20 -> small LLM reranker scores 0-10 -> top 10 -> add neighbouring sections as context.
9. **MCP vs Web UI** (img05): MCP exposes LLM-free retrieval primitives and the client agent orchestrates; the Web UI runs planner->executor->synthesis end to end.
10. **Projects** (img07): named bundles of shared sources; a default project on the user profile scopes queries.

**Image descriptions** (all viewed): img00 horizontal exploded 6-layer stack (cover); img01 three-panel raw thread -> structured artifact -> embedded row with the CKPT_PREFETCH=4 example; img02 query "restore hangs after manifest load" over four candidates (2w-old paraphrase thread, 1d-old exact-token message with ERR_MANIFEST_TIMEOUT, 3h-old "sounds good, thanks!" false neighbour, 8-month-old thread decayed) with the four signal cards; img03 five messages grouped in bursts, burst 01 filtered, burst 02 embedded; img04 isometric 6-layer stack; img05 MCP client (direct tool calls, raw evidence rows, client orchestrates) vs Web UI (planner, executor, synthesis); img06 six ranked lists (vector, FTS, thread summaries, graph, wiki vector, Slack FTS) + merged column with RRF scores 0.0792/0.0776/0.0640/0.0640/0.0476/0.0476; img07 compiler and platform projects sharing "shared incidents"; img08 Slack event flow; img09 planner fan-out to five tools into evidence and synthesis; img10 six sources into one embeddings table queried by MCP/Web UI/agents; img11 C++ CheckpointLoader chunked by class/method/if/for with naive-windows vs language-aware legend.

**What is notable**: it is *not* an alternative to RAG; it is "RAG done maturely": hybrid lexical+vector, distillation, rerank, planner. Its most reusable ideas are (a) distill-before-embed into question-shaped cards, (b) multiple cheap signals fused rank-wise, (c) exposing LLM-free primitives so any agent can orchestrate, (d) keeping everything in one store with one row shape. Fast inference (Cerebras advertises 2,500-3,000 tok/s on https://www.cerebras.ai/infcamp, vendor claim) is what makes LLM distillation, rerank and planning affordable at ingest and query time.

## 3. Topic research (details and URLs in `research/02-topic-research.md`)

- **Contextual Retrieval** (Anthropic, 2024): LLM-written chunk context before embedding and BM25 cut failed top-20 retrievals 5.7%->2.9%; +rerank ->1.9%. Generic summaries gave "very limited gains" - so *structured, query-shaped* distillation (Cerebras) is a different bet to test, not assume.
- **Cursor** (Nov 2025): grep + semantic search together beat grep alone: +12.5% avg QA accuracy (6.5-23.5% by model), larger on repos >=1,000 files.
- **Agentic/grep retrieval** (2026 papers): inline-delivered grep beat vector in 10/10 harness-model pairs on a 116-question LongMemEval subset, but file-based delivery flipped 5/10; harness choice mattered as much as retriever. Keyword agents reach >90% of RAG metrics; direct corpus interaction beats sparse/dense baselines on some BRIGHT/BEIR sets. HN caveat: token-hungry, degrades past ~100k files, paraphrase queries favour embeddings.
- **Long context / CAG**: CAG beats RAG on small bounded corpora (HotPotQA/SQuAD); LC beats RAG on average when resourced but at large cost (26x tokens in one 972-answer study: 73.1% vs 65.4%); lost-in-the-middle persists; Self-Route-style routing is the pragmatic answer.
- **PageIndex** (tree index + LLM reasoning, 39k stars): strong on single long documents, vendor-reported 98.7% FinanceBench; corpus-wide scaling is Cloud-only per its README.
- **Third-party reimplementation** of the Cerebras reranker (dev.to): MRR 0.57->0.90, but 31 questions on one corpus - anecdote, not evidence.

**Core insight**: published evidence conflicts by corpus type, harness, and delivery mode. Nobody can tell a team *for their corpus* whether they need vectors, distillation, an agent loop, or just the context window. Authors of "Is grep all you need" explicitly conclude teams must benchmark their whole configuration.

## 4. Open-source landscape (live data 2026-10-16)

Columns: license is the SPDX id from the GitHub API (NOASSERTION = custom/unrecognised file; Weaviate and pgvector are BSD-3 / PostgreSQL-style in practice per their repos - **[assessment]**, not verified). Strength/weakness text is **[assessment]** drawn from repo descriptions and READMEs I read (qmd and PageIndex READMEs read in full; others from GitHub description/search snippets).

| Project | License | Stars | Last push (UTC) | Architecture | Strength | Weakness / gap |
|---|---|---|---|---|---|---|
| [LangChain](https://github.com/langchain-ai/langchain) | MIT | 147,938 | 2026-10-16 | Orchestration framework; chains/agents; vectorstore + retriever abstractions | Huge ecosystem, integrations | Abstraction churn; RAG quality is up to you (assessment) |
| [LlamaIndex](https://github.com/run-llama/llama_index) | MIT | 52,524 | 2026-10-14 | Data framework: loaders, indices (vector, tree, KG), query engines | Many loaders/indices, strong RAG focus | Heavy; default chunk+vector path; evaluation is separate |
| [Haystack](https://github.com/deepset-ai/haystack) | Apache-2.0 | 26,748 | 2026-10-16 | Pipeline/graph of components (retriever, ranker, generator) | Explicit pipelines, hybrid + rerank components | Requires you to assemble and tune; no corpus-specific verdict |
| [RAGFlow](https://github.com/infiniflow/ragflow) | Apache-2.0 | 92,334 | 2026-10-16 | Full RAG engine/app: deep document parsing, chunk templates, agent workflows, own doc store | Strong parsing (PDF/tables), UI, citations | Heavy self-hosted stack (Docker, Elasticsearch/Infinity); fixed pipeline |
| [Dify](https://github.com/langgenius/dify) | NOASSERTION | 158,661 | 2026-10-16 | LLMOps platform with RAG pipelines and workflow builder | Low-code, large community | Platform lock-in; custom license (NOASSERTION in GitHub API) |
| [LightRAG](https://github.com/HKUDS/LightRAG) | MIT | 40,172 | 2026-10-15 | Graph + vector dual-level retrieval, LLM entity extraction at index time | Cheaper than GraphRAG, incremental updates | Index-time LLM cost; quality varies with extraction model (assessment) |
| [GraphRAG](https://github.com/microsoft/graphrag) | MIT | 36,361 | 2026-10-12 | LLM-built knowledge graph + community summaries for global questions | Good for corpus-wide 'global' questions | Expensive indexing; batch oriented |
| [txtai](https://github.com/neuml/txtai) | Apache-2.0 | 13,023 | 2026-10-16 | Embeddings DB (SQLite+ANN+graph) + workflows + RAG | Single-package, embeddings-DB with SQL | Vector-centric; limited eval tooling |
| [Vespa](https://github.com/vespa-engine/vespa) | Apache-2.0 | 7,129 | 2026-10-16 | Search/serving engine: BM25 + vector + tensor ranking, phased ranking | Production-grade hybrid ranking at scale | Operationally heavy for small teams |
| [Chroma](https://github.com/chroma-core/chroma) | Apache-2.0 | 29,513 | 2026-10-15 | Embedding database / search infra | Easiest dev experience | Storage layer only; no distillation or evaluation |
| [Qdrant](https://github.com/qdrant/qdrant) | Apache-2.0 | 35,103 | 2026-10-16 | Vector DB (Rust), filtering, hybrid/sparse support | Fast, filterable | Storage layer only |
| [Weaviate](https://github.com/weaviate/weaviate) | NOASSERTION | 16,887 | 2026-10-16 | Vector DB with hybrid (BM25+vector) and modules | Hybrid built in, modules | Storage layer; BSD-3 per repo (GitHub API shows NOASSERTION) |
| [pgvector](https://github.com/pgvector/pgvector) | NOASSERTION | 23,390 | 2026-10-15 | Vector similarity inside Postgres (HNSW/IVFFlat) | Same DB as app data (the Cerebras choice) | Storage layer; you build everything above it |
| [Milvus](https://github.com/milvus-io/milvus) | Apache-2.0 | 46,402 | 2026-10-16 | Distributed vector DB | Scale | Heavy to operate; storage layer |
| [RAGatouille](https://github.com/AnswerDotAI/RAGatouille) | Apache-2.0 | 3,968 | 2025-05-17 | ColBERT late-interaction retrieval wrapper | Strong retrieval quality, token-level matching | Last push 2025-05; large index; maintenance slowing |
| [ColBERT](https://github.com/stanford-futuredata/ColBERT) | MIT | 3,948 | 2025-10-14 | Late-interaction research implementation | SOTA-style retrieval | Research code; heavy |
| [Verba](https://github.com/weaviate/Verba) | BSD-3-Clause (archived) | 7,695 | 2026-06-08 | RAG chatbot app on Weaviate | Nice UI | Archived (read-only) |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | MIT | 67,209 | 2026-10-16 | All-in-one desktop/server chat-with-docs app, workspaces | Easy local app, workspaces (project scoping) | Chunk+vector default; limited retrieval tuning/explainability |
| [Kotaemon](https://github.com/Cinnamon/kotaemon) | Apache-2.0 | 25,809 | 2026-07-14 | Document chat UI with hybrid RAG, citations | Citations, hybrid + rerank | Last push 2026-07; app not library |
| [R2R](https://github.com/SciPhi-AI/R2R) | MIT | 8,023 | 2025-11-07 | Agentic RAG service with REST API, hybrid search, KG | API-first | Last push 2025-11; heavy stack |
| [Cognee](https://github.com/topoteretes/cognee) | Apache-2.0 | 32,403 | 2026-10-16 | AI memory: graph + vector, ECL pipeline | Memory for agents, graph | Graph/LLM heavy; early API churn (assessment) |
| [PageIndex](https://github.com/VectifyAI/PageIndex) | MIT | 39,182 | 2026-10-16 | Vectorless: LLM-built tree index + LLM tree search | No chunking/vector DB, traceable citations | Per-document focus; corpus scaling Cloud-only per README; high query-time LLM cost; text PDFs only locally |
| [CocoIndex](https://github.com/cocoindex-io/cocoindex) | Apache-2.0 | 11,710 | 2026-10-16 | Incremental indexing engine (used by Cerebras for code) | Incremental sync, lineage | Indexing layer only; no retrieval/eval |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Unlicense | 69,156 | 2026-08-04 | Regex search over files | Zero index, exact, fast | No semantics/ranking; token-hungry as agent tool |
| [mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | 67,305 | 2026-10-16 | Agent memory layer | Popular memory API | Memory, not corpus search |
| [Graphiti](https://github.com/getzep/graphiti) | Apache-2.0 | 31,818 | 2026-10-15 | Temporal knowledge graph for agents | Temporal facts | Needs graph DB; heavy |
| [Letta](https://github.com/letta-ai/letta) | Apache-2.0 | 25,166 | 2026-09-10 | Stateful agents with memory | Agent memory | Platform, not retrieval lib |
| [UltraRAG](https://github.com/OpenBMB/UltraRAG) | Apache-2.0 | 5,727 | 2026-10-14 | Low-code MCP framework for composing RAG pipelines/research | MCP-native composition, research focus | Pipeline authoring, not an eval-driven default |
| [RAG-Anything](https://github.com/HKUDS/RAG-Anything) | MIT | 23,621 | 2026-10-12 | Multimodal RAG built on LightRAG | Multimodal docs | Heavy; LightRAG dependency |
| [qmd](https://github.com/tobi/qmd) | MIT | 30,443 | 2026-10-15 | CLI hybrid search over docs/notes (FTS + vectors + rerank), MCP | Strong local UX, popular | Doc-centric; no thread distillation/bursts; no cross-strategy benchmark (assessment from README) |
| [CAG (reference impl)](https://github.com/hhhuang/CAG) | MIT | 1,607 | 2025-05-26 | KV-cache preload of entire corpus | No retrieval; fast per query | Bounded static corpora only; reference code, last push 2025-05 |
| [sqlite-rag-mcp](https://github.com/giuseppeferretti/sqlite-rag-mcp) | MIT | 0 | 2026-07-06 | SQLite FTS5 + sqlite-vec + RRF MCP | Single file, offline | 0 stars, young; plain chunks |
| [local-rag-mcp](https://github.com/Gilligan-Tech-Inc/local-rag-mcp) | NOASSERTION | 1 | 2026-08-12 | SQLite FTS5 + optional Ollama embeddings + RRF MCP | Graceful FTS-only fallback | 1 star; plain chunks |
| [mneme](https://github.com/AgentGameLab/mneme) | MIT | 7 | 2026-10-12 | Agent memory: FTS5+sqlite-vec+RRF MCP | Citations + trace validation | Memory-focused; 7 stars |
| [StrataFS](https://github.com/neul-labs/stratafs) | MIT | 2 | 2026-07-07 | Semantic filesystem: FTS5+vec+metadata over many stores via MCP | Many connectors | 2 stars; v0.2 |
| [Quaid](https://github.com/quaid-app/quaid) | NOASSERTION | 3 | 2026-06-25 | Local agent memory in Rust, SQLite FTS5+BGE vectors, 26 MCP tools | Local binary, graph path output | 3 stars; memory-focused |

Classes of approach and where they sit:

| Paradigm | Examples | When it wins | When it loses |
|---|---|---|---|
| Classic chunk + dense vector RAG | LangChain, LlamaIndex defaults, Chroma/Qdrant/pgvector | paraphrase queries, big corpora, cheap per query | exact identifiers, chunk context loss, stale data, sync/re-embed burden |
| Hybrid BM25+vector+rerank | Haystack, Vespa, Weaviate, qmd, Cerebras | most corpora; best default | still chunk-bound; tuning is manual |
| Contextual/distilled indexing | Anthropic contextual retrieval; Cerebras distillation | conversational/ticket/incident data | ingest-time LLM cost; no OSS turnkey implementation found |
| Graph RAG | GraphRAG, LightRAG, Cognee, Graphiti | corpus-wide "global" questions, entity relations | extraction cost and quality |
| Late interaction | ColBERT/RAGatouille | high-precision passage retrieval | index size; maintenance |
| Tree / reasoning index | PageIndex | long structured documents | per-query LLM cost; multi-doc scaling |
| Long context / CAG | CAG, prompt caching | small static corpora (<~200k tokens) | cost, lost-in-the-middle, changing data |
| Agentic grep / direct corpus interaction | Claude Code style, DCI paper | code, logs, verbatim evidence, changing data | tokens, latency, scale >100k files |
| Agent memory | mem0, Letta, Graphiti, mneme, Quaid | user/agent facts across sessions | not corpus search |

## 5. Gap analysis

1. **Crowded**: "SQLite + FTS5 + sqlite-vec + RRF + MCP" has at least 6 projects (qmd 30k stars, sqlite-rag-mcp, local-rag-mcp, mneme, StrataFS, Quaid). Building another one is not useful. **[assessment]**
2. **No turnkey OSS for distill-then-index of conversational/incident/ticket data** (question-shaped cards + same-author burst records with rarity gating + age decay). Found in the Cerebras post and described in pieces elsewhere (contextual retrieval), but I found no project offering it as a ready, tested, provider-agnostic component. (Search was broad but not exhaustive.)
3. **No cross-paradigm, corpus-specific evidence tool.** qmd bench compares its own four backends from hand-written fixtures. Nothing found automatically compares classic chunk-RAG vs hybrid vs distilled cards vs agentic grep vs full-context on *your* corpus with cost, latency and confidence intervals, and returns a recommendation.
4. **Evaluation gets skipped.** Anthropic ("always run evals"), the grep paper, and the reproducibility study all say results do not transfer between setups.
5. **Fast inference makes new trade-offs viable** (LLM at ingest + rerank + planning) but most OSS defaults still assume cheap-only retrieval and no LLM in the loop.

## 6. Decision

**Lodestone** (`drkwv34/lodestone-kb`): an embedding-optional, distillation-first knowledge engine in a single SQLite file, plus `lodestone bench`, a harness that tells you whether classic RAG, hybrid, distilled cards, an agentic loop or the whole context window is the right retrieval strategy *for your corpus*, with cost, latency and confidence intervals.

Why this and not alternatives considered:
- *Another vector-RAG framework / SQLite hybrid MCP*: rejected, crowded (gap 1).
- *Graph RAG*: rejected, heavy, covered by Microsoft/HKUDS/Cognee.
- *PageIndex clone*: rejected, well-funded incumbent, single-document focus.
- *CAG tool*: too narrow (bounded corpora) but included as a bench strategy.
- *Lodestone*: uses the post's most reusable ideas (distillation cards, multi-signal fusion, LLM-free primitives, projects, one row shape), works without embeddings (so works offline/free), and its bench answers the question the literature leaves open. Feasible as a compact MVP with deterministic fakes (no paid API needed in CI).

Risks (detail in SRS): crowded neighbourhood (qmd), LLM cost at ingest, benchmark validity (synthetic questions leak lexical overlap), distillation hallucination, scope creep. Mitigations are written into requirements (leakage metric, card provenance links, strict MVP boundary).

## 7. Sources

Post/blog: https://x.com/cerebras/status/2077822555159945507 (via https://api.fxtwitter.com/cerebras/status/2077822555159945507), https://www.cerebras.ai/blog/how-we-built-our-knowledge-base, https://www.cerebras.ai/infcamp
Commentary: https://dev.to/faridgnank02/rebuilding-the-cerebras-knowledge-base-an-llm-reranker-4016, https://datasciocean.com/en/paper-intro/cerebras-rag/, https://taeho.io/en/reading/how-cerebras-built-its-enterprise-knowledge-base_23624
Research: https://cursor.com/blog/semsearch, https://www.anthropic.com/news/contextual-retrieval, https://arxiv.org/abs/2412.15605, https://github.com/hhhuang/CAG, https://aclanthology.org/2024.emnlp-industry.66/, https://arxiv.org/html/2502.09977v2, https://arxiv.org/abs/2606.20898, https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long, https://arxiv.org/html/2605.27105, https://arxiv.org/html/2605.15184v1, https://latenteval.ai/research/is-grep-all-you-need, https://arxiv.org/html/2602.23368, https://www.scholarfeed.org/paper/2605.05242, https://news.ycombinator.com/item?id=48460863
Projects: all GitHub URLs in the table above; READMEs read: https://raw.githubusercontent.com/tobi/qmd/main/README.md, https://raw.githubusercontent.com/VectifyAI/PageIndex/main/README.md; SQLite-hybrid projects via https://github.com/giuseppeferretti/sqlite-rag-mcp, https://github.com/Gilligan-Tech-Inc/local-rag-mcp, https://github.com/AgentGameLab/mneme, https://stratafs.neullabs.com/, https://github.com/quaid-app/quaid
Name check (GitHub search + PyPI, 2026-10-16): `lodestone-kb` had 0 GitHub repos by that name, 404 on PyPI, and no `drkwv34/lodestone-kb` repo. Rejected: `cardex` (450 hits; PyPI 0.1.0 exists), `ragless` (RAGless exists), `cairn-kb` (exists).
