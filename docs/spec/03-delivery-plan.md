# 03 - Delivery plan: Lodestone (14 project-days)

Repo: `drkwv34/lodestone-kb` (to be created by the owner/REPO-BOT, see `04-repo-bootstrap.md`). One session = one project-day (a daily 11:00 AM GMT-5 run), done on a branch `day-NN-<slug>`, merged by PR after CI is green. Days 1-13 deliver the MVP; Day 14 is buffer + stretch + release candidate.

## 0. Rules that apply to every day

**Working rules for the implementing agent**
1. Read `docs/spec/01-SRS.md`, `docs/spec/02-architecture.md` and this file section for today before coding. Implement only today's requirement IDs. If a requirement is impossible as written, record a decision in `docs/decisions/NNNN-title.md` and continue; do not silently change scope.
2. Create/refresh an OpenSpec change for the day: `openspec/changes/day-NN-<slug>/` with `proposal.md`, `tasks.md`, and spec deltas whose requirement text quotes the FR/NFR IDs. Archive it when done. (Real OpenSpec only: output must come from the actual `openspec` CLI.)
3. Tests first or alongside; every FR has at least one test named with its ID (e.g. `def test_fr_035_rrf_reproduces_cerebras_figure`).
4. Never call a paid API in tests. Live-provider checks are manual, optional and must be clearly labelled.
5. Keep modules <= 500 lines, `mypy --strict`, `ruff`, coverage gate as in NFR-012 (gate ramps: Day 1-3 >= 70%, Day 4-8 >= 80%, Day 9+ >= 85%).
6. Commit style: small commits with Conventional Commit messages, authored by the repo owner identity configured for the repo (no `cursor[bot]`, no `Co-authored-by` trailers).
7. At the end: update `docs/PROGRESS.md` (a table: day, date, PR, CI URL, requirement IDs done, deviations) and tag `day-NN` on the merge commit.

**Definition of Done (every day) with pasted evidence** - the final PR description AND `docs/evidence/day-NN.md` must contain, pasted (not paraphrased):
- E1 `openspec validate day-NN-<slug> --strict` output (exit 0), and `openspec list` showing the change archived or active as appropriate.
- E2 CI run URL (GitHub Actions run page) with all required jobs green, plus the line `conclusion: success` from `gh run view <id> --json conclusion`.
- E3 Authorship check over the day's commits only (range = previous day's tag to HEAD):
  `git log day-(NN-1)..HEAD --format='%h %an <%ae> | %cn <%ce>' && git log day-(NN-1)..HEAD --format=%B | grep -ci 'co-authored-by\|cursor\[bot\]'` -> expected count `0`, and every author line equals the configured owner identity. (Day 1 range = from the first commit.) Using the day tag as the range start avoids failing on older commits.
- E4 `pytest -q` summary line and coverage percentage line.
- E5 Requirement checklist: each of today's IDs with the test name(s) proving it.
- E6 For days marked [UI-less] nothing else; no screenshots needed (CLI project) - instead paste a short terminal transcript of the day's demo command.
A day is NOT done if any of E1-E5 is missing, CI is red, or a covered requirement lacks a test. If blocked, open a PR titled `day-NN (partial)`, list what remains in `docs/PROGRESS.md`, and carry it to the next day's start (buffer day 14 absorbs up to one day of slip).

## 1. Day-by-day

### Day 1 - Scaffold, config, storage, CLI skeleton, CI
- **Objective**: installable package with `lodestone init`, config validation, SQLite schema v1 + migrations, CI.
- **Requirements**: FR-001, FR-002, FR-082, FR-080 (partial: Python/SQLite/FTS5 probe), NFR-011, NFR-012 (gates), NFR-017.
- **Deliverables**: `pyproject.toml` (hatchling), `src/lodestone/{config,storage,cli}`; migrations `0001_init.sql` (DDL from architecture 7.1 without eval tables); pydantic `Config` per 3.1; Typer app with `init`, `doctor`, `config show`; `.github/workflows/ci.yml`; LICENSE (Apache-2.0), NOTICE; `docs/spec/` copies of the four spec docs; `docs/PROGRESS.md`; `openspec/` initialised; pre-commit config.
- **Tests**: config valid/invalid fixtures (5 invalid cases), init idempotence E2E, migration apply + newer-version refusal, FTS5 probe, secret redaction (FR-005 preview).
- **DoD**: E1-E5 + `lodestone init && lodestone doctor` transcript.

### Day 2 - Tokenizer, term stats, FTS lanes, files connector (text/markdown)
- **Objective**: ingest a folder and search it lexically.
- **Requirements**: FR-010 (md/txt/rst), FR-030, FR-032 (infrastructure: term_stats/IDF), FR-014 (hash skeleton), FR-041 (filters: source/kind).
- **Deliverables**: `tokenize.py` (unicode-aware, identifier-preserving), `connectors/files.py` with path jail + gitignore, `ingest/pipeline.py` v0 (one record per file), FTS triggers, `term_stats` maintenance, query sanitiser + `fts_raw` and `fts_rare` lanes, `sync`, `search` (single-lane output), fixture corpora under `tests/fixtures/`.
- **Tests**: path traversal/symlink, ignored/binary/oversize files, sanitiser fuzz (1,000 strings), exact-token ranking (`ERR_MANIFEST_TIMEOUT` #1), IDF values vs hand-computed, resync no-op.
- **DoD**: E1-E5 + demo: `sync` + `search "ERR_MANIFEST_TIMEOUT"` transcript.

### Day 3 - Chunkers (markdown + code), incremental sync, projects and sources CLI
- **Requirements**: FR-015, FR-016, FR-014 (complete), FR-003, FR-004, FR-005, FR-010 (code kinds), `section`/`code` records with `parent_id`/`seq`.
- **Deliverables**: `chunking/markdown.py`, `chunking/code.py` (py/js/ts/go/java/c/cpp/rs tables), parent/child records, prune/tombstones, `source add/list/remove/sync`, projects in config + CLI scoping.
- **Tests**: heading-path goldens; code chunk goldens reproducing the class->method->if/for figure; sync-after-edit re-processes one file only (counted); source remove purges FTS/term_stats; project scoping property test (200 queries).
- **DoD**: E1-E5.

### Day 4 - Providers, FakeLLM, cost log, distillation cards
- **Requirements**: FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-060, FR-063, FR-031, FR-025 (S, if time).
- **Deliverables**: `providers/chat.py` (httpx, retry), `providers/fake.py`, local fake HTTP server fixture, `distill/{llm,heuristic,render}.py`, `prompts/card.v1.md`, card cache, `fts_card` lane, `cost` command, `llm_log`.
- **Tests**: malformed-JSON retry/fallback matrix, golden heuristic cards, cache hit rate, provider fault injection (200/429/500/timeout/truncated), cost totals property test, paraphrase fixture found only by `fts_card`.
- **DoD**: E1-E5 + transcript of `sync --provider fake` showing 0 LLM calls on resync.

### Day 5 - Threads connector, whole-thread upsert, bursts
- **Requirements**: FR-011, FR-012, FR-013, FR-020/FR-021 applied to threads.
- **Deliverables**: `connectors/threads.py` (JSONL streaming + line errors), `examples/slack_export_to_jsonl.py`, thread record rendering, burst builder + gate with config, `kind=burst` children carrying `context_prefix`, atomic replace on thread change.
- **Tests**: the 5-message burst example from the Cerebras figure (filtered vs embedded); thread append updates in place and removes old bursts; malformed JSONL; timezone parsing; `kind=burst` records searchable via lanes.
- **DoD**: E1-E5 + `examples/` demo transcript.

### Day 6 - Embeddings (optional), vector backends, vec lanes
- **Requirements**: FR-033, FR-061, FR-062 (partial: offline provider swap), FR-083 (vec reindex).
- **Deliverables**: `vectors/{embedder,hash,openai_compat,backends}.py`, brute-force and sqlite-vec backends with parity, `embeddings` writes in ingest (card/chunk/burst), `reindex --lanes vec`, `[vec]` extra, notices when vec lanes unavailable.
- **Tests**: hash determinism across runs, backend parity (1,000 vectors, 1e-6), model/dim mismatch handling, embeddings removed with records, offline guard test.
- **DoD**: E1-E5; note that sqlite-vec tests are skipped (not failed) when the extra is absent, but CI installs it on Ubuntu.

### Day 7 - Fusion: RRF, decay, rare-token weighting, dedupe/cap, expansion, explain, grep lane, perf baseline
- **Requirements**: FR-034, FR-035, FR-036, FR-037, FR-038, FR-040, FR-041 (complete), FR-042, NFR-001, NFR-002, NFR-003 (first measurements).
- **Deliverables**: `fusion/*.py`, `lanes/grep.py`, `search` pipeline orchestrator, evidence packet models + `schemas/evidence.v1.json`, `--explain`, perf tests (`pytest -m perf`).
- **Tests**: RRF reproduces 0.0792 from the Cerebras figure; decay ordering + floor; cap/diversity; neighbour expansion edge cases; explain contributions sum; filters property test (500 combos); regex guard; perf numbers printed.
- **DoD**: E1-E5 + perf numbers pasted (NFR-001..003) and, if above target, a decision record with a plan.

### Day 8 - Rerank, SDK, CLI polish
- **Requirements**: FR-039, FR-050, FR-051 (all non-bench, non-mcp, non-ask commands), FR-081, FR-064.
- **Deliverables**: `rerank.py`, `lodestone/__init__.py` facade (`Lodestone` class per architecture 4.1), `py.typed`, `search/grep/get/who-knows/recent/stats` CLI (`who-knows` and `recent` implemented here: FR-043, FR-044), query log, doctest README snippet.
- **Tests**: rerank permutation property; fallback identical to fused order; SDK mypy strict; CLI help snapshots; default query log stores no text.
- **DoD**: E1-E5.

### Day 9 - MCP server and `ask`
- **Requirements**: FR-052, FR-053, FR-054, FR-055 (S), FR-056, FR-043/044 exposed via MCP.
- **Deliverables**: `mcp_server.py` (6 read-only tools, DB opened `mode=ro`), `ask/{planner,executor,sufficiency,synthesis}.py`, injection test corpus (10 payloads), `docs/mcp.md` with Claude Code/Cursor config snippets.
- **Tests**: MCP client integration (list + call each tool, schema-validate), socket-blocking test in `--offline`, planner validation/fallback, citation validator, loop termination with adversarial FakeLLM, injection payloads.
- **DoD**: E1-E5 + transcript of a scripted MCP session.

### Day 10 - Bench I: formats, synthetic corpus, baseline strategies, metrics, report skeleton
- **Requirements**: FR-070, FR-071, FR-073 (classic-rag, bm25-chunks, hybrid-chunks, lodestone-lexical), FR-074 (retrieval + cost + latency metrics), FR-076 (skeleton), `window.py` chunker.
- **Deliverables**: `bench/{evalset,synth,metrics,runner,strategies/base.py,strategies/chunks.py,strategies/lodestone.py,report.py}`, `lodestone bench synth|run|report`, schemas `evalset.v1`, `report.v1`.
- **Tests**: metric goldens (hand-computed recall/MRR/nDCG), synth determinism (same seed byte-identical; hash pinned in test), strategies run on `--threads 60` corpus offline, parent-collapse correctness.
- **DoD**: E1-E5 + a generated `report.md` (offline, hash embedder caveat visible) pasted in evidence.

### Day 11 - Bench II: agentic and full-context strategies, question generation, statistics, advise
- **Requirements**: FR-072, FR-073 (rest: lodestone-hybrid, lodestone-rerank, agentic-ask, grep-agent, full-context), FR-074 (correctness, judge optional), FR-075, FR-077 (S), FR-078 (S).
- **Deliverables**: `bench/{questions.py,stats.py,advise.py,cache.py}`, strategies `grep_agent.py`, `full_context.py`, `agentic.py`, leakage metric, bootstrap CIs, paired diffs, advise rules R1-R4, resume cache.
- **Tests**: leakage filter, bootstrap on known distributions (seeded), paired significance flag, each advise rule with crafted reports, resume performs 0 duplicate LLM calls, `full-context` reports `skipped: too_large` when over budget.
- **DoD**: E1-E5 + full offline bench transcript < 5 min (NFR target) with `advise` output.

### Day 12 - Hardening: plugins, concurrency, security, crash safety, doctor --deep
- **Requirements**: FR-017, FR-018, FR-062 (complete), FR-080 (complete), FR-083 (complete), NFR-004, NFR-006, NFR-007, NFR-008, NFR-009, NFR-010, NFR-015.
- **Deliverables**: entry-point connector loader + `examples/plugin_demo/`, bounded concurrency, structured logging, `doctor --deep`, crash-injection test harness (SIGKILL 50 iterations), security tests (path jail, log scrubbing), import-linter config, 200k-record scale run documented (lexical-only) in `docs/benchmarks/scale.md`.
- **Tests**: as listed; fault injection across providers; ruff `S` rules clean.
- **DoD**: E1-E5 + crash-test summary and scale numbers pasted.

### Day 13 - Docs, examples, real-provider bench runs, packaging
- **Requirements**: NFR-013, NFR-016, NFR-014, FR-064 (docs), FR-078 (if left), release readiness for v0.1.0.
- **Deliverables**: README (from `04-repo-bootstrap.md`), docs (`quickstart`, `concepts`, `connectors`, `mcp`, `bench`, `privacy`, `faq`), `examples/quickstart.sh` executed in CI, wheel + sdist build verified with `pip install dist/*.whl` in a clean venv test, `docs/benchmarks/` with synthetic offline results and **clearly labelled** instructions for real-embedder runs; if the owner has provided provider env vars in the CI/session, run and commit one real run, else mark `status: not run - needs keys` in `FINDINGS.md` (never fabricate numbers).
- **Tests**: quickstart script, link check, wheel smoke.
- **DoD**: E1-E5 + `pip install` clean-venv transcript.

### Day 14 - Buffer, stretch, release candidate
- **Objective**: finish any partial days; then in order: FR-079 BEIR adapter; unfinished S requirements; Dockerfile for MCP; polish. Prepare `CHANGELOG.md` and `docs/RELEASE.md` for v0.1.0; tag `v0.1.0-rc1` (not `v0.1.0`, not PyPI) and stop.
- **Requirements**: remaining M first, then S, then C per SRS section 11.
- **DoD**: E1-E5 + requirements status table (all M must be green) + `docs/benchmarks/FINDINGS.md` honest hypothesis table (H1-H5: held / not held / not tested).

## 2. Critical path and slip policy
Day 1 -> 2 -> 3 -> 4 -> 5 -> 7 -> 8 -> 9 are sequential; Day 6 (vectors) can slip behind Day 7 if needed because lexical lanes do not depend on it (swap order, update PROGRESS.md). Bench days (10-11) depend on 2-8. If two days slip, drop in this order: FR-079, FR-055, FR-077, FR-078, FR-025, FR-043/044.

## 3. Day-to-requirement coverage check (every M requirement appears)
FR-001/002 D1; FR-003/004/005 D3; FR-010 D2-3; FR-011/012/013 D5; FR-014 D2-3; FR-015/016 D3; FR-017 D12; FR-020-026 D4; FR-030-032 D2/D4/D2; FR-033 D6; FR-034-038, 040-042 D7; FR-039 D8; FR-050/051 D8 (+D9 for mcp/ask, D10-11 bench commands); FR-052-056 D9; FR-060/063 D4; FR-061 D6; FR-062 D6/D12; FR-070/071 D10; FR-072 D11; FR-073 D10-11; FR-074/075 D10-11; FR-076 D10 (+D13); FR-080 D1/D12; FR-081 D8; FR-082 D1; FR-083 D6/D12.
