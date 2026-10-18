# 04 - Repository bootstrap: lodestone-kb

Created by the owner *before* the workspace foundation (the research session did not create any repo). Nothing here is to be published to PyPI automatically.

## 1. Identity
- GitHub repo: `drkwv34/lodestone-kb` (checked 2026-10-16: GitHub API returns 404 = free; PyPI `lodestone-kb` = 404 = free).
- Python distribution name `lodestone-kb`; import package `lodestone`; CLI `lodestone`.
- License: Apache-2.0 (`LICENSE` full text, `NOTICE`). Every source file starts with an SPDX line `# SPDX-License-Identifier: Apache-2.0`.
- Description (GitHub About, <= 120 chars): `Embedding-optional knowledge engine: distilled cards, explainable hybrid search, MCP, and a RAG-strategy benchmark.`
- Topics: `rag`, `retrieval`, `sqlite`, `fts5`, `mcp`, `knowledge-base`, `llm`, `benchmark`, `python`, `agents`.
- Default branch `main`; branch protection recommended (CI required); daily branches `day-NN-<slug>`.

## 2. Directory layout
```
lodestone-kb/
  README.md  LICENSE  NOTICE  CHANGELOG.md  CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md
  pyproject.toml  .pre-commit-config.yaml  .gitignore  .editorconfig  importlinter.ini
  lodestone.example.toml
  .github/
    workflows/ci.yml  workflows/release.yml
    ISSUE_TEMPLATE/{bug_report.md,feature_request.md}  PULL_REQUEST_TEMPLATE.md  dependabot.yml
  openspec/                      # OpenSpec project (specs + changes/day-NN-*)
  docs/
    spec/{00-research-summary.md,01-SRS.md,02-architecture.md,03-delivery-plan.md,04-repo-bootstrap.md}
    decisions/                   # NNNN-title.md decision records
    evidence/day-NN.md           # pasted DoD evidence per day
    benchmarks/{FINDINGS.md,scale.md}
    {quickstart,concepts,connectors,mcp,bench,privacy,faq}.md
    PROGRESS.md
  schemas/{evidence.v1.json,evalset.v1.json,report.v1.json,config.v1.json}
  src/lodestone/
    __init__.py  py.typed  cli.py  sdk.py  config.py  models.py  tokenize.py  errors.py
    storage/{db.py,migrations/0001_init.sql}
    connectors/{base.py,files.py,threads.py,plugins.py}
    chunking/{markdown.py,code.py,window.py}
    ingest/{pipeline.py,derived.py}
    distill/{llm.py,heuristic.py,render.py}
    prompts/{card.v1.md,rerank.v1.md,planner.v1.md,synth.v1.md,sufficiency.v1.md,qgen.v1.md}
    providers/{chat.py,fake.py,offline.py}
    vectors/{embedder.py,hash.py,openai_compat.py,backends.py}
    lanes/{fts.py,rare.py,vec.py,grep.py}
    fusion/{rrf.py,decay.py,collapse.py,expand.py}
    retrieval.py  rerank.py  mcp_server.py
    ask/{planner.py,executor.py,sufficiency.py,synthesis.py}
    bench/{evalset.py,synth.py,questions.py,metrics.py,stats.py,runner.py,cache.py,report.py,advise.py,strategies/}
  tests/
    fixtures/  unit/  integration/  e2e/  bench/  perf/
  examples/{quickstart.sh,slack_export_to_jsonl.py,plugin_demo/}
```

## 3. `pyproject.toml` essentials
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[project]
name = "lodestone-kb"
version = "0.1.0.dev0"
description = "Embedding-optional knowledge engine with distilled cards, explainable hybrid search, MCP and a RAG-strategy benchmark."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
dependencies = ["typer>=0.12", "httpx>=0.27", "pydantic>=2.7", "mcp>=1.2", "pathspec>=0.12", "rich>=13"]
[project.optional-dependencies]
vec = ["sqlite-vec>=0.1", "numpy>=1.26"]
dev = ["pytest>=8", "pytest-cov", "hypothesis", "mypy", "ruff", "import-linter", "pre-commit", "pip-licenses"]
[project.scripts]
lodestone = "lodestone.cli:app"
[project.entry-points."lodestone.connectors"]
files = "lodestone.connectors.files:FilesConnector"
threads = "lodestone.connectors.threads:ThreadsConnector"
[tool.ruff]
line-length = 100
select = ["E","F","I","B","UP","S","SIM","RUF"]
[tool.mypy]
strict = true
[tool.pytest.ini_options]
markers = ["perf: performance tests", "network: needs network (opt-in)"]
addopts = "-q --strict-markers -m 'not perf and not network'"
```
(Dependency versions are lower bounds. Checked on PyPI 2026-10-16: mcp 2.3.0, sqlite-vec 0.1.9, pathspec 1.1.1, typer 0.27.3, hatchling 1.32.4; npm `@fission-ai/openspec` 1.14.2. Workspace foundation must re-verify; MCP and ask must check the current `mcp` SDK server API (it is at major version 2, so `FastMCP` import paths may differ from older docs) and record any deviation in `docs/decisions/`. FTS5 `tokenchars '_-'` tokenizer syntax was smoke-tested on SQLite 3.46.1.)

## 4. CI workflow (`.github/workflows/ci.yml`)
```yaml
name: ci
on: { push: { branches: [main] }, pull_request: {} }
permissions: { contents: read }
jobs:
  lint-type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev,vec]"
      - run: ruff check . && ruff format --check .
      - run: mypy src
      - run: lint-imports
  test:
    needs: lint-type
    strategy:
      fail-fast: false
      matrix:
        include:
          - { os: ubuntu-latest, python: "3.11" }
          - { os: ubuntu-latest, python: "3.12" }
          - { os: ubuntu-latest, python: "3.13" }
          - { os: macos-latest, python: "3.12" }
          - { os: windows-latest, python: "3.12", smoke: true }
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -e ".[dev,vec]"
      - run: pytest --cov=src/lodestone --cov-report=term-missing --cov-fail-under=${{ vars.COV_GATE || 70 }}
        if: matrix.smoke != true
      - run: pytest tests/e2e -k smoke
        if: matrix.smoke == true
  perf:
    needs: test
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev,vec]"
      - run: pytest -m perf -s
  openspec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: npm i -g @fission-ai/openspec   # verify the package name during workspace foundation; record in decisions if different
      - run: openspec validate --all --strict
  licenses:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev,vec]" && pip-licenses --format=markdown --fail-on="GPL;AGPL"
```
Coverage gate is raised per the delivery plan (set repo variable `COV_GATE` to 70, 80, 85 at workspace foundation, distillation cards, and MCP and ask). The `release.yml` workflow (docs and packaging) builds wheel+sdist on tags `v*`, uploads them as workflow artifacts and a draft GitHub release; it contains **no** PyPI publish step.

## 5. README skeleton
```markdown
# Lodestone
> Embedding-optional knowledge engine: distilled cards, explainable hybrid search, an MCP server, and a benchmark that tells you which RAG strategy your corpus actually needs.

[badges: ci, license Apache-2.0, python]

## Why
- Classic RAG = chunk + embed + top-k. It loses exact tokens, thread context and freshness, and nobody tells you if it was worth it.
- Lodestone distils threads/docs into question-shaped *cards*, searches with several cheap signals (exact tokens, rare terms, recency, optional vectors), shows *why* each hit ranked, and ships `lodestone bench` to compare classic RAG, hybrid, cards, agentic grep and full-context **on your data**.
- Inspired by Cerebras' "How we built our knowledge base" (2026). Not affiliated.

## Quickstart (offline, 2 minutes)
pip install lodestone-kb
lodestone init && lodestone source add docs --kind files --path ./docs
lodestone sync --offline && lodestone search "ERR_MANIFEST_TIMEOUT" --explain

## Features / How it compares (honest table vs qmd, SQLite-hybrid MCP servers, PageIndex)
## MCP (Claude Code / Cursor config)
## Benchmark (`lodestone bench synth|run|report|advise`) + caveats (hash embedder is not semantic)
## Privacy and data flow
## Roadmap / Out of scope
## Contributing - License Apache-2.0
```

## 6. Contribution docs (content outline)
- `CONTRIBUTING.md`: dev setup (`pip install -e ".[dev,vec]"`, `pre-commit install`), running tests (`pytest`, `pytest -m perf`), requirement-ID test naming, OpenSpec change workflow, commit style, "no paid APIs in tests", how to write a connector (link to `docs/connectors.md`).
- `CODE_OF_CONDUCT.md`: Contributor Covenant 2.1 (verbatim text to be copied during workspace foundation).
- `SECURITY.md`: private reporting via GitHub security advisories; scope (path jail, injection, secrets); supported versions table.
- Issue/PR templates: bug template asks for `lodestone doctor` output; PR template carries the DoD checklist (E1-E5).

## 7. Pre-implementation checklist (owner, one session before workspace foundation)
1. Create empty public repo `drkwv34/lodestone-kb` (no auto-generated license; workspace foundation adds Apache-2.0). *This is an irreversible public action: needs the owner's approval.*
2. Add `docs/spec/` with the five documents + `docs/PROGRESS.md` (empty table).
3. Set repo variable `COV_GATE=70`; enable Actions; set the commit identity for the repo to the owner's.
4. Confirm provider secrets are NOT required (none for CI). Optional: `CEREBRAS_API_KEY` as a repository secret only if the owner wants real benchmark runs during docs and packaging.
5. Start the workspace foundation next.
