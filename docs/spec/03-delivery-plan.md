# 03 - Delivery plan: Lodestone (feature roadmap)

Repo: `drkwv34/lodestone-kb` (created by the owner; see `04-repo-bootstrap.md`). Each feature lands on a branch `feat/<slug>`, merged by PR after CI is green. The first thirteen features deliver the MVP; the last item is buffer, stretch and a release candidate.

## 0. Rules that apply to every feature

**Working rules for contributors**
1. Read `docs/spec/01-SRS.md`, `docs/spec/02-architecture.md` and this file section for the feature before coding. Implement only that feature's requirement IDs. If a requirement is impossible as written, record a decision in `docs/decisions/NNNN-title.md` and continue; do not silently change scope.
2. Create/refresh an OpenSpec change for the feature: `openspec/changes/<slug>/` with `proposal.md`, `tasks.md`, and spec deltas whose requirement text quotes the FR/NFR IDs. Archive it when done. (Real OpenSpec only: output must come from the actual `openspec` CLI.)
3. Tests first or alongside; every FR has at least one test named with its ID (e.g. `def test_fr_035_rrf_reproduces_cerebras_figure`).
4. Never call a paid API in tests. Live-provider checks are manual, optional and must be clearly labelled.
5. Keep modules <= 500 lines, `mypy --strict`, `ruff`, coverage gate as in NFR-012 (gate ramps: workspace foundation through structural chunkers >= 70%, distillation through fusion >= 80%, MCP and later >= 85%).
6. Commit style: small commits with Conventional Commit messages, authored by the repo owner identity configured for the repo (no `cursor[bot]`, no `Co-authored-by` trailers).
7. At the end: update `docs/PROGRESS.md` (a table: feature, date, PR, CI URL, requirement IDs done, deviations) and tag the merge commit with the feature slug.

**Definition of Done (every feature) with pasted evidence** - the final PR description AND `docs/evidence/<feature>.md` must contain, pasted (not paraphrased):
- E1 `openspec validate <slug> --strict` output (exit 0), and `openspec list` showing the change archived or active as appropriate.
- E2 CI run URL (GitHub Actions run page) with all required jobs green, plus the line `conclusion: success` from `gh run view <id> --json conclusion`.
- E3 Authorship check over the feature's commits only (range = previous feature tag to HEAD):
  `git log <previous-tag>..HEAD --format='%h %an <%ae> | %cn <%ce>' && git log <previous-tag>..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'` -> expected count `0`, and every author line equals the configured owner identity. (Workspace foundation range = from the first commit.) Using the previous feature tag as the range start avoids failing on older commits.
- E4 `pytest -q` summary line and coverage percentage line.
- E5 Requirement checklist: each of the feature's IDs with the test name(s) proving it.
- E6 For features marked [UI-less] nothing else; no screenshots needed (CLI project) - instead paste a short terminal transcript of the feature's demo command.
A feature is NOT done if any of E1-E5 is missing, CI is red, or a covered requirement lacks a test. If blocked, open a PR titled `<slug> (partial)`, list what remains in `docs/PROGRESS.md`, and carry it into the next feature (the buffer/release-candidate slot absorbs limited slip).

## 1. Feature sequence

### Workspace foundation - Scaffold, config, storage, CLI skeleton, CI
- **Objective**: installable package with `lodestone init`, config validation, SQLite schema v1 + migrations, CI.
- **Requirements**: FR-001, FR-002, FR-082, FR-080 (partial: Python/SQLite/FTS5 probe), NFR-011, NFR-012 (gates), NFR-017.
- **Deliverables**: `pyproject.toml` (hatchling), `src/lodestone/{config,storage,cli}`; migrations `0001_init.sql` (DDL from architecture 7.1 without eval tables); pydantic `Config` per 3.1; Typer app with `init`, `doctor`, `config show`; `.github/workflows/ci.yml`; LICENSE (Apache-2.0), NOTICE; `docs/spec/` copies of the four spec docs; `docs/PROGRESS.md`; `openspec/` initialised; pre-commit config.
- **Tests**: config valid/invalid fixtures (5 invalid cases), init idempotence E2E, migration apply + newer-version refusal, FTS5 probe, secret redaction (FR-005 preview).
- **DoD**: E1-E5 + `lodestone init && lodestone doctor` transcript.

### Lexical search - Tokenizer, term stats, FTS lanes, files connector (text/markdown)
- **Objective**: ingest a folder and search it lexically.
- **Requirements**: FR-010 (md/txt/rst), FR-030, FR-032 (infrastructure: term_stats/IDF), FR-014 (hash skeleton), FR-041 (filters: source/kind).
- **Deliverables**: `tokenize.py` (unicode-aware, identifier-preserving), `connectors/files.py` with path jail + gitignore, `ingest/pipeline.py` v0 (one record per file), FTS triggers, `term_stats` maintenance, query sanitiser + `fts_raw` and `fts_rare` lanes, `sync`, `search` (single-lane output), fixture corpora under `tests/fixtures/`.
- **Tests**: path traversal/symlink, ignored/binary/oversize files, sanitiser fuzz (1,000 strings), exact-token ranking (`ERR_MANIFEST_TIMEOUT` #1), IDF values vs hand-computed, resync no-op.
- **DoD**: E1-E5 + demo: `sync` + `search "ERR_MANIFEST_TIMEOUT"` transcript.

### Structural chunkers and sources - Chunkers (markdown + code), incremental sync, projects and sources CLI
- **Requirements**: FR-015, FR-016, FR-014 (complete), FR-003, FR-004, FR-005, FR-010 (code kinds), `section`/`code` records with `parent_id`/`seq`.
- **Deliverables**: `chunking/markdown.py`, `chunking/code.py` (py/js/ts/go/java/c/cpp/rs tables), parent/child records, prune/tombstones, `source add/list/remove/sync`, projects in config + CLI scoping.
- **Tests**: heading-path goldens; code chunk goldens reproducing the class->method->if/for figure; sync-after-edit re-processes one file only (counted); source remove purges FTS/term_stats; project scoping property test (200 queries).
- **DoD**: E1-E5.

### Distillation cards - Providers, FakeLLM, cost log, distillation cards
- **Requirements**: FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-060, FR-063, FR-031, FR-025 (S, if time).
- **Deliverables**: `providers/chat.py` (httpx, retry), `providers/fake.py`, local fake HTTP server fixture, `distill/{llm,heuristic,render}.py`, `prompts/card.v1.md`, card cache, `fts_card` lane, `cost` command, `llm_log`.
- **Tests**: malformed-JSON retry/fallback matrix, golden heuristic cards, cache hit rate, provider fault injection (200/429/500/timeout/truncated), cost totals property test, paraphrase fixture found only by `fts_card`.
- **DoD**: E1-E5 + transcript of `sync --provider fake` showing 0 LLM calls on resync.

### Threads connector - Threads connector, whole-thread upsert, bursts
- **Requirements**: FR-011, FR-012, FR-013, FR-020/FR-021 applied to threads.
- **Deliverables**: `connectors/threads.py` (JSONL streaming + line errors), `examples/slack_export_to_jsonl.py`, thread record rendering, burst builder + gate with config, `kind=burst` children carrying `context_prefix`, atomic replace on thread change.
- **Tests**: the 5-message burst example from the Cerebras figure (filtered vs embedded); thread append updates in place and removes old bursts; malformed JSONL; timezone parsing; `kind=burst` records searchable via lanes.
- **DoD**: E1-E5 + `examples/` demo transcript.

### Vector embeddings - Embeddings (optional), vector backends, vec lanes
- **Requirements**: FR-033, FR-061, FR-062 (partial: offline provider swap), FR-083 (vec reindex).
- **Deliverables**: `vectors/{embedder,hash,openai_compat,backends}.py`, brute-force and sqlite-vec backends with parity, `embeddings` writes in ingest (card/chunk/burst), `reindex --lanes vec`, `[vec]` extra, notices when vec lanes unavailable.
- **Tests**: hash determinism across runs, backend parity (1,000 vectors, 1e-6), model/dim mismatch handling, embeddings removed with records, offline guard test.
- **DoD**: E1-E5; note that sqlite-vec tests are skipped (not failed) when the extra is absent, but CI installs it on Ubuntu.

### Hybrid fusion - Fusion: RRF, decay, rare-token weighting, dedupe/cap, expansion, explain, grep lane, perf baseline
- **Requirements**: FR-034, FR-035, FR-036, FR-037, FR-038, FR-040, FR-041 (complete), FR-042, NFR-001, NFR-002, NFR-003 (first measurements).
- **Deliverables**: `fusion/*.py`, `lanes/grep.py`, `search` pipeline orchestrator, evidence packet models + `schemas/evidence.v1.json`, `--explain`, perf tests (`pytest -m perf`).
- **Tests**: RRF reproduces 0.0792 from the Cerebras figure; decay ordering + floor; cap/diversity; neighbour expansion edge cases; explain contributions sum; filters property test (500 combos); regex guard; perf numbers printed.
- **DoD**: E1-E5 + perf numbers pasted (NFR-001..003) and, if above target, a decision record with a plan.

### Rerank and SDK - Rerank, SDK, CLI polish
- **Requirements**: FR-039, FR-050, FR-051 (all non-bench, non-mcp, non-ask commands), FR-081, FR-064.
- **Deliverables**: `rerank.py`, `lodestone/__init__.py` facade (`Lodestone` class per architecture 4.1), `py.typed`, `search/grep/get/who-knows/recent/stats` CLI (`who-knows` and `recent` implemented here: FR-043, FR-044), query log, doctest README snippet.
- **Tests**: rerank permutation property; fallback identical to fused order; SDK mypy strict; CLI help snapshots; default query log stores no text.
- **DoD**: E1-E5.

### MCP and ask - MCP server and `ask`
- **Requirements**: FR-052, FR-053, FR-054, FR-055 (S), FR-056, FR-043/044 exposed via MCP.
- **Deliverables**: `mcp_server.py` (6 read-only tools, DB opened `mode=ro`), `ask/{planner,executor,sufficiency,synthesis}.py`, injection test corpus (10 payloads), `docs/mcp.md` with Claude Code/Cursor config snippets.
- **Tests**: MCP client integration (list + call each tool, schema-validate), socket-blocking test in `--offline`, planner validation/fallback, citation validator, loop termination with adversarial FakeLLM, injection payloads.
- **DoD**: E1-E5 + transcript of a scripted MCP session.

### Benchmark I - Formats, synthetic corpus, baseline strategies, metrics, report skeleton
- **Requirements**: FR-070, FR-071, FR-073 (classic-rag, bm25-chunks, hybrid-chunks, lodestone-lexical), FR-074 (retrieval + cost + latency metrics), FR-076 (skeleton), `window.py` chunker.
- **Deliverables**: `bench/{evalset,synth,metrics,runner,strategies/base.py,strategies/chunks.py,strategies/lodestone.py,report.py}`, `lodestone bench synth|run|report`, schemas `evalset.v1`, `report.v1`.
- **Tests**: metric goldens (hand-computed recall/MRR/nDCG), synth determinism (same seed byte-identical; hash pinned in test), strategies run on `--threads 60` corpus offline, parent-collapse correctness.
- **DoD**: E1-E5 + a generated `report.md` (offline, hash embedder caveat visible) pasted in evidence.

### Benchmark II - Agentic and full-context strategies, question generation, statistics, advise
- **Requirements**: FR-072, FR-073 (rest: lodestone-hybrid, lodestone-rerank, agentic-ask, grep-agent, full-context), FR-074 (correctness, judge optional), FR-075, FR-077 (S), FR-078 (S).
- **Deliverables**: `bench/{questions.py,stats.py,advise.py,cache.py}`, strategies `grep_agent.py`, `full_context.py`, `agentic.py`, leakage metric, bootstrap CIs, paired diffs, advise rules R1-R4, resume cache.
- **Tests**: leakage filter, bootstrap on known distributions (seeded), paired significance flag, each advise rule with crafted reports, resume performs 0 duplicate LLM calls, `full-context` reports `skipped: too_large` when over budget.
- **DoD**: E1-E5 + full offline bench transcript < 5 min (NFR target) with `advise` output.

### Hardening - Plugins, concurrency, security, crash safety, doctor --deep
- **Requirements**: FR-017, FR-018, FR-062 (complete), FR-080 (complete), FR-083 (complete), NFR-004, NFR-006, NFR-007, NFR-008, NFR-009, NFR-010, NFR-015.
- **Deliverables**: entry-point connector loader + `examples/plugin_demo/`, bounded concurrency, structured logging, `doctor --deep`, crash-injection test harness (SIGKILL 50 iterations), security tests (path jail, log scrubbing), import-linter config, 200k-record scale run documented (lexical-only) in `docs/benchmarks/scale.md`.
- **Tests**: as listed; fault injection across providers; ruff `S` rules clean.
- **DoD**: E1-E5 + crash-test summary and scale numbers pasted.

### Docs and packaging - Docs, examples, real-provider bench runs, packaging
- **Requirements**: NFR-013, NFR-016, NFR-014, FR-064 (docs), FR-078 (if left), release readiness for v0.1.0.
- **Deliverables**: README (from `04-repo-bootstrap.md`), docs (`quickstart`, `concepts`, `connectors`, `mcp`, `bench`, `privacy`, `faq`), `examples/quickstart.sh` executed in CI, wheel + sdist build verified with `pip install dist/*.whl` in a clean venv test, `docs/benchmarks/` with synthetic offline results and **clearly labelled** instructions for real-embedder runs; if the owner has provided provider env vars in the CI/session, run and commit one real run, else mark `status: not run - needs keys` in `FINDINGS.md` (never fabricate numbers).
- **Tests**: quickstart script, link check, wheel smoke.
- **DoD**: E1-E5 + `pip install` clean-venv transcript.

### Buffer and release candidate - Buffer, stretch, release candidate
- **Objective**: finish any partial features; then in order: FR-079 BEIR adapter; unfinished S requirements; Dockerfile for MCP; polish. Prepare `CHANGELOG.md` and `docs/RELEASE.md` for v0.1.0; tag `v0.1.0-rc1` (not `v0.1.0`, not PyPI) and stop.
- **Requirements**: remaining M first, then S, then C per SRS section 11.
- **DoD**: E1-E5 + requirements status table (all M must be green) + `docs/benchmarks/FINDINGS.md` honest hypothesis table (H1-H5: held / not held / not tested).

## 2. Critical path and slip policy
Workspace foundation -> lexical search -> structural chunkers and sources -> distillation cards -> threads connector -> hybrid fusion -> rerank and SDK -> MCP and ask are sequential; vector embeddings can slip behind hybrid fusion if needed because lexical lanes do not depend on it (swap order, update PROGRESS.md). Benchmark I and II depend on lexical search through rerank and SDK. If two features slip, drop in this order: FR-079, FR-055, FR-077, FR-078, FR-025, FR-043/044.

## 3. Feature-to-requirement coverage check (every M requirement appears)
FR-001/002 workspace foundation; FR-003/004/005 structural chunkers; FR-010 lexical search then chunkers; FR-011/012/013 threads; FR-014 lexical search then chunkers; FR-015/016 chunkers; FR-017 hardening; FR-020-026 distillation; FR-030-032 lexical search / distillation / lexical search; FR-033 vectors; FR-034-038, 040-042 fusion; FR-039 rerank; FR-050/051 rerank and SDK (+MCP for mcp/ask, benchmark I-II for bench commands); FR-052-056 MCP; FR-060/063 distillation; FR-061 vectors; FR-062 vectors/hardening; FR-070/071 benchmark I; FR-072 benchmark II; FR-073 benchmark I-II; FR-074/075 benchmark I-II; FR-076 benchmark I (+docs and packaging); FR-080 workspace foundation/hardening; FR-081 rerank; FR-082 workspace foundation; FR-083 vectors/hardening.
