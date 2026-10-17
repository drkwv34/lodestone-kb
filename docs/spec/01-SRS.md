# 01 - Software Requirements Specification: Lodestone (lodestone-kb)

Version 1.0 - 2026-10-16 - Style: IEEE 830 / ISO 29148 adapted. Language: English.
Companion docs: `00-research-summary.md` (why), `02-architecture.md` (how), `03-delivery-plan.md` (when), `04-repo-bootstrap.md` (repo).

## 1. Introduction

### 1.1 Purpose
Specify an open-source Python project, **Lodestone**, an *embedding-optional, distillation-first knowledge engine* with a built-in *strategy benchmark*. It lets a person or team index conversational, document and code corpora into one local SQLite file, retrieve evidence through explainable LLM-free primitives (CLI, SDK, MCP), optionally answer questions with citations, and measure, on their own corpus, whether classic chunk+vector RAG, hybrid search, distilled cards, an agentic loop, or full-context prompting is the better retrieval strategy.

### 1.2 Scope
In scope (MVP, v0.1.0): local single-user/single-node engine; connectors for files and generic JSONL threads; chunking; LLM distillation to "cards"; burst records; lexical + optional vector + grep lanes; RRF fusion with recency decay and rarity signals; optional LLM rerank; project scoping; Python SDK; CLI; MCP stdio server; `ask` agent pipeline with citations; benchmark harness with synthetic corpus, question generation, 8 strategies, metrics, statistics, report and recommendation.
Out of scope: see section 9.

### 1.3 Definitions
- **Record**: one retrievable unit (doc, section, code chunk, thread, burst) in the `records` table.
- **Card**: LLM-distilled structured summary of a record: `question`, `summary`, `resolution`, `entities[]`, `code_refs[]`.
- **Burst**: run of consecutive same-author messages in a thread, indexed separately if it passes a signal gate.
- **Lane**: one ranked retrieval list (e.g. `fts_raw`, `fts_card`, `fts_rare`, `vec_card`, `vec_chunk`, `grep`).
- **RRF**: Reciprocal Rank Fusion, score(d)=sum_l w_l/(k+rank_l(d)), default k=60.
- **Project**: named bundle of sources defining default query scope.
- **Strategy**: a complete retrieval(+answer) configuration evaluated by the bench.
- **Provider**: an OpenAI-compatible HTTP endpoint (chat and/or embeddings) or a local fake.

### 1.4 References
Cerebras, "How we built our knowledge base" (2026-07-15), https://www.cerebras.ai/blog/how-we-built-our-knowledge-base; Anthropic Contextual Retrieval; Cormack et al. 2009 (RRF); Li et al. EMNLP-Industry 2024 (RAG vs LC); full list in `00-research-summary.md` section 7.

## 2. Overall description

### 2.1 Product perspective
Standalone Python package + CLI + MCP server. No server infrastructure. One SQLite database file per workspace (`.lodestone/index.db`). Talks only to user-configured LLM/embedding endpoints (or none, in `--offline` mode). Complements, does not replace, vector databases.

### 2.2 Differentiation vs existing OSS (from the survey)
| Capability | qmd | SQLite-hybrid MCP servers | PageIndex | Lodestone |
|---|---|---|---|---|
| FTS5 + RRF + MCP | yes | yes | no | yes (table stakes) |
| Distilled question-shaped cards for threads | no | no | no | **yes** |
| Burst records with rarity/engagement gate | no | no | no | **yes** |
| Age decay as first-class signal | no | metadata only | no | **yes** |
| Works with zero embeddings/zero LLM | partial (BM25 mode) | partial | no | **yes (offline mode is a tested configuration)** |
| Cross-paradigm benchmark with auto-generated questions, cost, latency, CI | no (own 4 backends, manual fixtures) | no | vendor benchmarks | **yes** |
| Recommendation verdict | no | no | no | **yes (`advise`)** |

### 2.3 User classes and personas
- **P1 Dana, platform engineer** (primary): 40 Slack-export channels, wiki, 5 repos; wants an MCP server her team's coding agents can call; needs to justify skipping a vector DB.
- **P2 Ravi, ML/search engineer**: evaluating RAG options; wants a reproducible, honest comparison on his corpus with confidence intervals.
- **P3 Mei, solo developer / researcher**: laptop only, no budget, wants offline notes search with citations.
- **P4 Connector author**: adds a source via a plugin.
- **P5 Maintainer/agent** (REPO-BOT): implements the repo day by day, needs unambiguous requirements and tests.

### 2.4 Operating environment
Python 3.11-3.13; Linux, macOS (CI), Windows (best effort, CI smoke); SQLite >= 3.38 with FTS5 (bundled in CPython builds; `doctor` verifies); optional `sqlite-vec`. Network only to configured providers.

### 2.5 Constraints
C-1 License of the project Apache-2.0; all dependencies must be Apache-2.0/MIT/BSD-compatible.
C-2 No paid API required to run CI or the default test suite (FakeLLM/FakeEmbedder).
C-3 One developer-agent session = one delivery day (see delivery plan); modules must be independently testable.
C-4 No telemetry. No network calls unless the user configures a provider and runs a command that needs it.
C-5 Core runtime dependencies <= 8 (typer, httpx, pydantic, mcp, plus 4 more at most); pure-Python wheel.

### 2.6 Assumptions
A-1 Users have corpora from 100 to 200,000 records; above ~1M records is unsupported in v0.x.
A-2 An OpenAI-compatible chat endpoint is available for distillation/rerank/ask (Cerebras, OpenAI, Ollama, vLLM, LM Studio all qualify); the embedding endpoint is optional.
A-3 Slack-like data is supplied as exported JSONL; live Slack ingestion is out of MVP.
A-4 The Cerebras post's burst gate combines IDF>=4.0, >=200 chars and reactions but does not publish the exact formula; Lodestone's weighted formula (FR-013) is our design, configurable, and validated by the bench rather than claimed equal.

## 3. Personas' key scenarios (use cases)
- UC-1 Index a docs folder and a Slack-export JSONL, search with `lodestone search "ERR_MANIFEST_TIMEOUT"`; see which lane found it and why (P1, P3).
- UC-2 Point Claude Code/Cursor at `lodestone mcp` and let the agent call `search`, `grep`, `get_record`, `who_knows` (P1).
- UC-3 Run `lodestone bench run --corpus ./my-corpus.toml` and read `report.md` with a verdict (P2).
- UC-4 Ask "who fixed the NFS stall and how?" with `lodestone ask` and get a cited answer (P1, P3).
- UC-5 Write a connector plugin in <60 lines (P4).

## 4. Functional requirements
Priority: M = must (MVP), S = should (MVP if time, else v0.2), C = could. Each has acceptance criteria (AC) testable by automated test unless noted. Test layer: U unit, I integration, E2E CLI, B bench.

### 4.1 Workspace, configuration, projects
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-001 | M | `lodestone init [PATH]` creates `lodestone.toml` and `.lodestone/index.db` with schema version stamped | Running twice is idempotent (second run exits 0, prints "already initialised"); DB `PRAGMA user_version` equals current schema version; E2E test |
| FR-002 | M | Config in TOML validated by pydantic; unknown keys rejected with the key path in the message | Invalid config -> exit code 2 and message containing `sources[0].kind`-style path; U test with 5 invalid fixtures |
| FR-003 | M | Projects: named sets of sources; one `default` project; commands accept `--project`; default project configurable | Search with `--project a` never returns records of sources not in `a` (property test over 200 random queries on fixture) |
| FR-004 | M | Source registry CRUD via CLI (`source add/list/remove/sync`) and TOML | `source remove` deletes its records, FTS rows, embeddings, term stats contributions (verified by row counts = 0 and df recount) |
| FR-005 | S | Environment overrides `LODESTONE_*` for secrets (API keys never stored in TOML by default) | Config dump (`lodestone config show`) redacts values of keys matching `*key*`, `*token*`, `*secret*` |

### 4.2 Connectors and ingestion
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-010 | M | `files` connector: globs include/exclude, honours `.gitignore`, supported kinds `md, txt, rst, py, js, ts, go, java, c, cpp, rs, json, yaml, toml`; skips binaries and files > `max_file_bytes` (default 1 MiB) | Fixture tree with ignored, binary and oversize files: only expected paths ingested; skip reasons logged |
| FR-011 | M | `threads` connector reads JSONL: one object per thread `{thread_id, channel?, title?, messages:[{id, author, ts(ISO-8601), text, reactions?:int}]}`; also accepts a Slack-export-to-JSONL helper script in `examples/` | Malformed lines are skipped with line numbers reported; valid lines ingested; ts parsed to UTC |
| FR-012 | M | Thread semantics: a thread is ONE record `kind=thread`; re-ingesting a changed thread replaces the record, its card, its bursts and embeddings atomically (one transaction) | Appending a message to a thread changes `updated_at` and `content_hash`, keeps `id`, old bursts removed; I test |
| FR-013 | M | Burst records: group consecutive same-author messages; a burst is indexed iff `score >= threshold` where `score = w_idf*[max_token_idf >= idf_min] + w_len*[chars >= min_chars] + w_react*[reactions>=1]` with defaults `idf_min=4.0, min_chars=200, w_idf=1, w_len=1, w_react=1, threshold=1.0` (any single signal passes by default; configurable); bursts store the thread title/question as `context_prefix` | Table-driven unit test with the 5-message example from the Cerebras figure: the short common-token burst is filtered, the long rare-term reacted-to burst is kept; thresholds configurable |
| FR-014 | M | Incremental sync: records keyed by `(source_id, ext_id)`; `content_hash` (SHA-256 of normalised raw text + chunker version) decides re-processing; deleted upstream items are tombstoned then purged by `sync --prune` | Second sync of unchanged corpus performs 0 LLM calls, 0 writes to `records` (counted); changing one file re-processes only that file |
| FR-015 | M | Markdown/text structural chunking: split on headings, then paragraphs; target 400 tokens (approx. 1 token = 4 chars default tokenizer; configurable), max 800; heading path stored as `title` (e.g. `Guide > Install > Linux`) | Chunks never exceed max; heading path correct on fixtures; code fences never split unless > max |
| FR-016 | M | Code chunking, regex coarse-to-fine for py/js/ts/go/java/c/cpp/rs: class/struct -> function/method -> block; file-level record (`kind=code_file`, signature outline) plus function-level (`kind=code`) records | Fixture file reproduces the class->method->if/for splitting behaviour from the Cerebras figure (deterministic expected chunks) |
| FR-017 | M | Connector plugin API: entry-point group `lodestone.connectors`; interface `Connector.discover(config) -> Iterable[RawItem]` with `ext_id, kind_hint, text, metadata, updated_at`; documented example <= 60 lines | Example plugin in `examples/` is loaded through entry points in an integration test |
| FR-018 | S | Ingest concurrency: bounded worker pool for LLM calls (`llm.max_concurrency`, default 4) with retry/backoff | Under injected 429/500 faults, ingest completes; max concurrency never exceeded (instrumented test) |

### 4.3 Distillation (cards)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-020 | M | For `thread`, `doc` and (configurable) `code_file` records, call the configured chat model with a versioned prompt (`prompts/card.v1.md`) returning JSON `{question, summary, resolution, entities[], code_refs[]}` validated by a pydantic schema; invalid JSON retried up to 2 times then falls back to FR-021 | With FakeLLM returning malformed JSON twice then valid: card stored; returning malformed 3 times: heuristic card stored and `card_method='heuristic'` |
| FR-021 | M | Heuristic card (no LLM): question = title or first sentence ending in `?` else first line; summary = first 2 sentences (<= 300 chars); resolution = last message of thread or empty; entities = top 5 capitalised/identifier-like terms by IDF; code_refs = regex matches for `[A-Z][A-Z0-9_]{3,}`, `snake_case_with_underscore`, `CamelCase`, `path/with/slash.ext`, error-code patterns | Deterministic output on fixtures (golden files); runs with zero network |
| FR-022 | M | `norm_text` = `question + "\n" + summary + "\n" + resolution + "\nsystems: " + entities + "\ncode: " + code_refs` (XML-tagged variant selectable); raw text is NOT embedded when a card exists (config `embed.source = card|raw|both`, default `card`) | Embedding input in test equals the expected string; changing config re-queues embeddings only |
| FR-023 | M | Card cache keyed by `(content_hash, prompt_version, model)`; re-running ingest after a model change regenerates only when `--refresh-cards` or key mismatch | Cache hit ratio 100% on rerun; changed model => regeneration count equals record count |
| FR-024 | M | Provenance: every card stores `source_message_ids` or char spans; `get_record` returns the raw text beside the card so any claim is checkable | Card-to-raw link present for 100% of cards in fixture |
| FR-025 | S | Contextual prefix (Anthropic style) for chunk records: optional 50-100-token LLM context stored in `context_prefix`, indexed in FTS and embeddings | Config flag `chunks.contextualize=true`; FakeLLM test verifies prefix appears in FTS-matchable text |
| FR-026 | M | Cost accounting: every LLM/embedding call logged with tokens in/out, latency, model; `lodestone cost` summarises per operation using a configurable price table | Summary totals equal sum of log rows (property test) |

### 4.4 Retrieval
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-030 | M | Lane `fts_raw`: FTS5 BM25 over raw text/title with column weights (`title` 3.0, `text` 1.0); query sanitiser turns user input into a safe FTS5 expression (phrases, prefix `*`, OR-expansion) | Fuzz test: 1,000 random strings never raise SQL errors; exact error token query (e.g. `ERR_MANIFEST_TIMEOUT`) ranks the containing record #1 on fixture |
| FR-031 | M | Lane `fts_card`: FTS5 over `norm_text` | Paraphrase fixture where only the card shares tokens is found by this lane and not by `fts_raw` |
| FR-032 | M | Lane `fts_rare`: restricts query to tokens with IDF >= `rare_idf` (default 4.0) and requires >=1 match; protects short rare-token messages from filler | "sounds good, thanks" never ranks above a rare-token record for a rare-token query (test from Cerebras example) |
| FR-033 | S | Optional vector lanes `vec_card` and `vec_chunk` using the configured embedder; storage via sqlite-vec when importable else exact brute-force cosine; same results (tolerance 1e-6) on both backends | Parity test on 1,000 vectors; with embeddings disabled these lanes are skipped and a notice is returned in `result.notices` |
| FR-034 | M | Lane `grep`: regex/literal search over raw text of in-scope records (SQLite `REGEXP` function registered in Python, or `rg` if on PATH and source is `files`), with line numbers and context lines | Regex fixture returns exact line spans; catastrophic-regex guard: per-query timeout 2 s and pattern length <= 500 |
| FR-035 | M | Fusion: weighted RRF with `k=60` default over enabled lanes; weights per lane in config; ties broken by `updated_at` desc then id | Unit test reproduces the Cerebras figure: six lists with ranks (2,3,1,5,5 across five lists) yield 0.0792 +/- 0.0001 |
| FR-036 | M | Recency decay: multiplicative factor `max(floor, 0.5 ** (age_days / half_life_days))` applied post-fusion; `half_life_days` and `floor` per source kind in config (defaults: thread 120 d/0.4, doc none, code none); can be disabled per query | Two otherwise-equal threads 8 months vs 2 weeks old: newer ranks first; floor respected; `--no-decay` restores raw order |
| FR-037 | M | Dedupe and diversity: collapse multiple records of the same parent (`parent_id`) into the best-scoring one, keep `matched_children`; per-source cap `max_per_source` (default 3) in the top `candidate_pool` (default 20) | Fixture with 6 chunks from one file: at most 3 appear; result lists the file once with children |
| FR-038 | M | Neighbour expansion: for chunk/section hits, attach previous and next siblings (`expand=1` default) with their heading text, never exceeding `expand_max_chars` (default 4,000) | Hit in middle section returns 3 sections in order; first/last handle missing neighbours |
| FR-039 | S | LLM rerank: send query + top `candidate_pool` snippets (<= 1,200 chars each) to the chat model, JSON schema `[{id, score 0-10}]`; keep top `rerank_keep` (default 10); on any error/timeout/malformed output fall back to fused order and add a notice | FakeLLM tests: valid reorder; malformed -> fallback order identical to no-rerank; recall@10 never lower than without rerank (property: rerank only permutes the pool) |
| FR-040 | M | Explainability: `--explain` / `explain=True` returns for each hit per-lane rank and score, RRF contribution, decay factor, rerank score, final score | JSON schema test; sum of contributions x decay equals reported score within 1e-9 |
| FR-041 | M | Filters: by project, source, kind, author, date range (`since`, `until`), metadata equality; applied before fusion so every hit satisfies them | Property test: 500 random filter combinations, 0 violations |
| FR-042 | M | Evidence packet schema (stable, versioned `evidence.v1`): `id, source, kind, title, uri, snippet, text?, score, lanes, updated_at, author(s), card?, children[], neighbours[]` | JSON-schema file in `schemas/`; all outputs validated in tests |
| FR-043 | S | `who_knows(topic)`: ranks authors by (number of in-scope records matching topic lanes weighted by recency and burst/reaction presence); returns top 5 with example record ids | Fixture with known experts returns the expected top-1 |
| FR-044 | S | `recent(n, since, filters)`: most recent records | Deterministic ordering test |

### 4.5 Interfaces: SDK, CLI, MCP, ask
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-050 | M | Python SDK: `Lodestone.open(path)`, `.sync()`, `.search(query, **opts) -> SearchResult`, `.get(id)`, `.grep(pattern, **opts)`, `.ask(question, **opts) -> Answer`, `.stats()`; fully typed (py.typed), no global state | mypy --strict passes on public API; doc-tested README snippet |
| FR-051 | M | CLI commands: `init, source (add|list|remove|sync), sync, search, grep, get, who-knows, recent, ask, mcp, cost, stats, doctor, bench (run|generate|report|advise), config show`; global `--json`, `--project`, `--offline`, `--db`; exit codes 0 ok, 1 runtime error, 2 usage/config error, 3 provider error | Each command has an E2E test; `--help` text snapshot-tested |
| FR-052 | M | MCP server (stdio; official `mcp` SDK) exposing tools `search`, `grep`, `get_record`, `list_sources`, `who_knows`, `recent`; every tool LLM-free except `search(rerank=true)`; JSON-schema'd inputs; output = `evidence.v1`; read-only (no write tools) | MCP client integration test lists 6 tools and calls each; tool results validate against schema; process makes no network call with `--offline` (socket-blocking test) |
| FR-053 | M | `ask`: planner -> parallel executor -> evidence normalisation -> synthesis with numbered citations `[n]` mapping to evidence ids; refuses to answer (returns `insufficient_evidence: true`) when evidence packet is empty | FakeLLM test: answer text contains only citation numbers that exist; empty evidence -> refusal |
| FR-054 | M | Planner: small LLM call sees a compact catalog (projects, sources, kinds, counts, date ranges, top terms) and returns tool calls (`search`, `grep`, `who_knows`, `recent`) with args as JSON; invalid plan -> default plan (`search` + `grep` if query contains identifier-like token) | Plan-validation tests; fallback is deterministic |
| FR-055 | S | Sufficiency loop: after synthesis-draft, a cheap check asks "is the evidence sufficient?" and may issue at most `ask.max_rounds - 1` (default 2 extra) follow-up tool rounds with refined queries; every round's calls logged | Loop terminates <= max_rounds in all tests incl. adversarial FakeLLM that always says insufficient |
| FR-056 | M | Untrusted content handling: all retrieved text placed inside `<evidence id=..>` blocks with an instruction hierarchy note; tool-call arguments chosen by planner restricted to the allow-list; prompt-injection fixture ("ignore previous instructions...") in a document must not alter tool selection in tests with a rule-based FakeLLM stub | Injection test suite (10 payloads) passes |

### 4.6 Providers
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-060 | M | OpenAI-compatible chat client (httpx): base_url, model, api_key_env, timeout, retries with exponential backoff + jitter, JSON mode when supported else tolerant JSON extraction | Tested against a local fake HTTP server (pytest fixture) for 200, 429, 500, timeout, truncated JSON |
| FR-061 | M | Embedder interface `embed(list[str]) -> list[list[float]]`; implementations `openai_compat`, `hash` (deterministic feature hashing, 256-d, for tests/offline demo only) | Hash embedder deterministic across runs and platforms |
| FR-062 | M | `--offline` / `offline=true` guarantees no outbound network: providers are replaced by hash embedder and heuristic cards; any attempt to use a remote provider raises `OfflineError` | Test with socket patched to raise: full ingest+search+bench(offline strategies) succeed |
| FR-063 | M | Deterministic `FakeLLM`: scripted responses + rule-based mode (cards from heuristic, rerank by token overlap, planner default plan) used in tests and `--provider fake` | All unit/integration tests run with no network; FakeLLM behaviour documented |
| FR-064 | S | Provider presets in docs for Cerebras, OpenAI, Ollama (config examples), no provider-specific code paths except optional `response_format` flag | Doc snippets validated by config-schema test |

### 4.7 Benchmark (`lodestone bench`)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-070 | M | Eval set format `evalset.v1` JSONL: `{qid, question, gold_ids[], gold_answer_must_contain[] ?, category, source_hint?}`; gold ids refer to `ext_id` of records (strategy-independent); validation command | Invalid sets rejected with line numbers |
| FR-071 | M | Synthetic corpus generator `lodestone bench synth --seed N --threads 300`: deterministic threads, docs and code snippets with controlled difficulty categories: `exact_token`, `paraphrase`, `stale_vs_fresh`, `tangent_in_long_thread`, `multi_source`, `unanswerable`; emits corpus + evalset; same seed => byte-identical output | Hash of output stable across 3 platforms in CI |
| FR-072 | M | Question generation from a real corpus: sample records (stratified by source/kind), ask LLM for 1-3 questions per record that a user would ask without quoting text; compute **leakage score** = Jaccard overlap of question tokens with gold-record tokens; drop questions above `leakage_max` (default 0.5); store category tags | With FakeLLM: leakage computed; filter drops expected questions; report includes leakage histogram |
| FR-073 | M | Strategy interface `Strategy.index(corpus)`, `Strategy.retrieve(question, k) -> list[id]`, optional `Strategy.answer(question) -> str`; built-in strategies: `classic-rag` (fixed 512-token windows, 64 overlap, dense only), `bm25-chunks`, `hybrid-chunks` (BM25+dense RRF), `lodestone-lexical` (cards+raw FTS lanes, no embeddings), `lodestone-hybrid` (adds vec lanes), `lodestone-rerank` (+LLM rerank), `agentic-ask` (ask pipeline), `grep-agent` (LLM with grep/read tools only), `full-context` (whole corpus in prompt when <= `context_budget_tokens`, else marked `skipped: too_large`) | Each strategy runs on the synthetic corpus with FakeLLM/hash embedder in CI; skipped strategies are reported as such, never silently omitted |
| FR-074 | M | Metrics: retrieval recall@{1,5,10,20}, MRR, nDCG@10 against gold ids (parent-collapsed so chunk and card strategies are comparable); answer correctness by `must_contain` substring match and optional LLM-judge (`--judge`); cost: tokens in/out and USD from price table; latency p50/p95/p99 per query; index build time and bytes | Metric functions verified against hand-computed examples (golden tests) |
| FR-075 | M | Statistics: 95% bootstrap CIs (default 2,000 resamples, seeded) per metric; paired bootstrap difference vs a chosen baseline (default `classic-rag`) with `significant` flag when the CI excludes 0; per-category breakdown | Seeded results reproducible; test with known synthetic scores |
| FR-076 | M | Report: `report.md` and `report.json` containing config hash, corpus hash, versions, per-strategy table, per-category table, cost/latency table, leakage stats, caveats section (auto-text: "hash embedder is not semantic" when used), and failures | Report golden-file test (stable ordering, no timestamps in body except header) |
| FR-077 | S | `lodestone bench advise`: rule-based verdict from the report. Rules (documented, deterministic): (R1) if `lodestone-lexical` recall@10 is within 3 pp of the best embedding strategy (paired CI includes 0) => "embeddings do not pay for themselves on this corpus"; (R2) if `full-context` is feasible and its correctness CI is >= best retrieval strategy and cost/query <= 3x => "consider context stuffing + caching"; (R3) if cards beat classic-rag significantly on `paraphrase` or `tangent_in_long_thread` => "distillation helps"; (R4) else "hybrid default". Each rule outputs evidence lines referencing report cells | Unit tests for each rule with crafted reports |
| FR-078 | S | Bench resume: results cached per (strategy, config hash, corpus hash, qid); an interrupted run resumes without re-spending tokens | Kill-and-resume test performs 0 duplicate LLM calls |
| FR-079 | C | BEIR/SciFact adapter (`bench import beir:scifact`) downloading from the public mirror with checksum verification | Optional extra; skipped in CI unless `LODESTONE_NETWORK_TESTS=1` |

### 4.8 Operations
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-080 | M | `doctor`: reports Python/SQLite versions, FTS5 availability, sqlite-vec availability, DB schema version, provider reachability (only if configured and not offline), config problems; exit 1 if any error | Test with FTS5-disabled stub reports error |
| FR-081 | M | Query log table (query hash, project, lanes, latency, result count; query text stored only if `log.store_queries=true`) and `stats` command | Default stores no query text (test) |
| FR-082 | M | Schema migrations: forward-only numbered SQL migrations applied transactionally; opening a DB with a newer schema than the code fails with a clear error | Test upgrading fixture DBs v1->vN; downgrade refused |
| FR-083 | S | `reindex --lanes fts|vec|cards` rebuilds derived data from stored raw text without re-contacting sources | Row counts identical before/after on fixture |

## 5. Non-functional requirements
| ID | Category | Requirement (measurable) | Verification |
|---|---|---|---|
| NFR-001 | Performance | Lexical `search` (fts_raw+fts_card+fts_rare, fusion, no rerank) p95 <= 50 ms at 20,000 records on a 2024-class laptop; CI gate 150 ms on GitHub-hosted runner | perf test (`pytest -m perf`) over synthetic corpus; result in CI log |
| NFR-002 | Performance | Heuristic-card ingest throughput >= 200 records/s (excluding embeddings) on same corpus | perf test |
| NFR-003 | Performance | Incremental no-change sync of 20,000 records completes in <= 10 s | perf test |
| NFR-004 | Scalability | Supports 200,000 records, DB <= 2 GB without embeddings (lexical only), documented memory <= 500 MB RSS during search | manual benchmark recorded in docs/benchmarks |
| NFR-005 | Determinism | Same input, same config, FakeLLM => byte-identical `search --json` and `bench` reports (excluding header timestamp) | golden tests |
| NFR-006 | Reliability | Ingest is transactional per record; killing the process mid-sync never leaves a record without its FTS row (consistency check in `doctor --deep`) | crash-injection test (SIGKILL at random points, 50 iterations) |
| NFR-007 | Reliability | Provider failures degrade gracefully: cards -> heuristic; rerank -> fused order; vec lanes -> skipped with notice; `ask` -> error with partial evidence | fault-injection tests |
| NFR-008 | Security | Files connector refuses paths outside configured roots (symlink and `..` traversal tested); no secrets in logs/reports; API keys only from env | security tests; log grep test |
| NFR-009 | Security | Prompt-injection hardening per FR-056; MCP server read-only; no shell execution anywhere in core; `rg` invoked with argument arrays only | tests + code scan in CI (`ruff S` rules) |
| NFR-010 | Privacy | `--offline` makes zero network connections; default config sends only card-prompt text (record raw text) and rerank snippets to the configured provider; documented data-flow table in docs | socket test; doc review checklist |
| NFR-011 | Portability | CI matrix: Python 3.11, 3.12, 3.13 on Ubuntu; 3.12 on macOS and Windows (smoke subset) | CI |
| NFR-012 | Quality | Line coverage >= 85% for `src/lodestone` (excluding `bench/strategies/*_live.py`); `mypy --strict` clean; `ruff` clean | CI gates |
| NFR-013 | Usability | Time to first search from `pip install` <= 5 minutes following README with `--offline` (manual check recorded in docs) | documented walkthrough + `examples/quickstart.sh` runs in CI |
| NFR-014 | Maintainability | Public API semver; deprecations warn for one minor; each module <= 500 lines (lint) | lint rule/CI script |
| NFR-015 | Observability | Structured logs (JSON when `LODESTONE_LOG=json`), per-operation timing, cost log; no PII in logs by default | tests |
| NFR-016 | Accessibility of docs | README, quickstart, concepts, bench guide, connector guide, MCP guide present and link-checked | CI link check |
| NFR-017 | Licensing | `LICENSE` Apache-2.0; `NOTICE`; dependency license report generated in CI shows no GPL/AGPL | CI step |
| NFR-018 | Supply chain | Dependencies pinned by lower bound + lockfile for dev; Dependabot config; no network access during tests other than the optional network marker | CI |

## 6. External interface requirements
- **User interface**: CLI only (no web UI in MVP). Human tables via `rich` optional; `--json` always available.
- **Software interfaces**: OpenAI-compatible REST (`/v1/chat/completions`, `/v1/embeddings`); MCP over stdio; Python entry points for connectors; SQLite file format documented in `02-architecture.md`.
- **Data interfaces**: `evidence.v1`, `evalset.v1`, `report.v1` JSON schemas in `schemas/`; threads JSONL.
- **Hardware**: none special; runs on CPU.

## 7. Data requirements (summary; DDL in architecture doc)
Entities: `meta`, `projects`, `sources`, `project_sources`, `records`, `records_fts` (FTS5), `cards` (inside records JSON + `card_cache`), `term_stats`, `embeddings`, `llm_log`, `query_log`, `eval_runs`, `eval_results`. All timestamps stored UTC ISO-8601. Raw text stored verbatim; derived data rebuildable (FR-083).

## 8. Evaluation methodology and benchmark plan (for the project itself)
Purpose: produce honest evidence on when each paradigm wins, and validate Lodestone's claims. Not marketing: negative results are published.

**Corpora**
1. `synth-support` (generated, seed 42, 300 threads, ~700 questions) - plumbing + controlled difficulty categories. With the hash embedder it validates *machinery only*; no claim about semantic quality is allowed from hash-embedder runs (the report caveat is mandatory, FR-076).
2. `self-docs` - Lodestone's own markdown docs + source (small, real, reproducible).
3. Optional real runs by the maintainer with a real embedder (e.g. a local Ollama model or an API) and a real chat model on (1) and (2); results stored in `docs/benchmarks/` with config hash. (Requires user-supplied keys; not part of CI.)
4. Stretch: BEIR SciFact (FR-079).

**Baselines**: `classic-rag` (dense, fixed windows 512/64, top-k as in metrics), `bm25-chunks`, `hybrid-chunks`, `grep-agent`, `full-context`; Lodestone variants as in FR-073.

**Hypotheses to test (not assumed)**
- H1: On `paraphrase` and `tangent_in_long_thread`, `lodestone-hybrid` improves recall@5 over `classic-rag` by >= 10 pp.
- H2: On `exact_token`, `lodestone-lexical` is within 3 pp of `lodestone-hybrid`.
- H3: On `stale_vs_fresh`, decay raises the correct (fresh) answer rank over `--no-decay` in >= 80% of paired cases.
- H4: Cards cost X tokens/record at ingest; report break-even number of queries vs per-query savings of reranking/fewer chunks.
- H5: `full-context` wins accuracy when corpus <= budget but costs >= 5x per query (report actual).

**Protocol**: fixed seeds; 3 repetitions for LLM-involved strategies at temperature 0; CIs per FR-075; leakage max 0.5; report config hash; failures counted as misses (never dropped); price table dated in the report.
**Success criteria for v0.1.0**: all MUST requirements verified; bench runs end-to-end offline in CI < 5 minutes; at least one real-embedder report published with caveats; honest verdict file `docs/benchmarks/FINDINGS.md` states which hypotheses held.

## 9. Out of scope (v0.1.0)
Web UI; multi-user auth/RBAC; hosted service; live Slack/Jira/Confluence connectors (JSONL import only; plugin API enables later); knowledge-graph/graph-RAG; multimodal (images, PDFs OCR; plain-text PDFs only via optional extra - not in MVP); fine-tuning embedding models; distributed storage; Postgres backend; streaming answers; non-English-specific tokenisation (default tokenizer is unicode-aware lowercase word split; quality on CJK not guaranteed).

## 10. Risks
| ID | Risk | Likelihood/Impact | Mitigation |
|---|---|---|---|
| R-1 | Seen as "another SQLite hybrid search" next to qmd (30k stars) | H/H | Lead with cards+bursts+bench; README comparison honest; do not compete on UX polish |
| R-2 | Synthetic questions leak lexical overlap and flatter BM25 | H/M | Leakage score + filter (FR-072); paraphrase category; caveats |
| R-3 | Distillation hallucinates facts | M/H | Provenance (FR-024); raw text always returned; cards used for retrieval, `ask` cites raw spans |
| R-4 | LLM ingest cost surprises users | M/M | Cost accounting (FR-026), `--dry-run` estimating tokens, heuristic fallback, caching |
| R-5 | 13-day schedule slips | M/M | Strict MVP boundary (S/C items are droppable), daily DoD, buffer day 14 |
| R-6 | Hash embedder results mistaken for real | M/H | Mandatory caveat, docs, report flag |
| R-7 | sqlite-vec packaging issues | M/L | Optional extra + brute-force fallback with parity test |
| R-8 | Agentic strategies non-deterministic | H/M | temperature 0, 3 reps, CIs, caching |
| R-9 | Prompt injection via indexed content | M/H | FR-056, read-only MCP, allow-listed tools |
| R-10 | Windows path/regex issues | M/L | Best-effort smoke tests only |

## 11. MVP boundary (decision rule)
MVP = all **M** requirements. **S** requirements are done in the order listed on Day 13-14 if time remains; **C** is never started before v0.1.0 is tagged. A requirement may be downgraded only via a recorded decision in `docs/decisions/`.

## 12. Traceability matrix (requirement -> design -> test -> day)
| Req | Architecture section | Test file (planned) | Day |
|---|---|---|---|
| FR-001,002,003,004,005 | 3.1 config, 3.2 CLI | tests/test_config.py, tests/e2e/test_init.py | 1, 3 |
| FR-010,014,015,016 | 3.3 connectors, chunkers | tests/test_files_connector.py, test_chunkers.py | 2, 3 |
| FR-011,012,013 | 3.3 threads, bursts | tests/test_threads.py, test_bursts.py | 5 |
| FR-017 | 3.3 plugins | tests/test_plugins.py | 12 |
| FR-018 | 3.4 ingest pipeline | tests/test_concurrency.py | 12 |
| FR-020..026 | 3.5 distillation | tests/test_cards.py, test_cost.py | 4 |
| FR-030..032, 034 | 3.6 lanes | tests/test_lanes.py | 2, 7 |
| FR-033, 061 | 3.7 embeddings | tests/test_vectors.py | 6 |
| FR-035..038, 040..042 | 3.8 fusion | tests/test_fusion.py, test_decay.py | 7 |
| FR-039 | 3.9 rerank | tests/test_rerank.py | 8 |
| FR-043, 044, 052 | 3.10 MCP | tests/test_mcp.py | 9 |
| FR-050 | 4.1 SDK | tests/test_sdk.py | 8 |
| FR-051 | 4.2 CLI | tests/e2e/test_cli.py | 1-9 incremental |
| FR-053..056 | 3.11 ask | tests/test_ask.py, test_injection.py | 9 |
| FR-060, 062, 063, 064 | 3.12 providers | tests/test_llm_client.py, test_offline.py | 4, 12 |
| FR-070..076 | 5 bench | tests/bench/*.py | 10, 11 |
| FR-077, 078 | 5 bench advise/resume | tests/bench/test_advise.py | 11, 13 |
| FR-079 | 5 bench BEIR | tests/bench/test_beir.py (network marker) | 14 (stretch) |
| FR-080..083 | 6 ops | tests/test_doctor.py, test_migrations.py | 1, 12 |
| NFR-001..004 | 8 perf | tests/perf/ | 7, 12 |
| NFR-005..018 | 9 quality attrs | CI configuration | 1, 12, 13 |
