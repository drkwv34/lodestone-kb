# Contributor guide

Lodestone is an embedding-optional local knowledge engine: distilled cards,
explainable hybrid search, a planned MCP server, and a planned RAG-strategy
benchmark. Work stays local by default. Optional chat and embedding providers
are OpenAI-compatible HTTP only; tests must not call paid APIs.

This file is for human contributors and AI assistants. Project conventions live
here; Cursor always applies `.cursor/rules/project.mdc`, which points back to
this guide. OpenSpec Cursor skills live under `.cursor/skills/` and slash
commands under `.cursor/commands/` (`/opsx-propose`, `/opsx-apply`,
`/opsx-archive`, `/opsx-explore`, `/opsx-sync`, `/opsx-update`).

## Layout and architecture

```
src/lodestone/          import package (CLI entry: lodestone.cli:app)
  cli.py                Typer CLI
  workspace.py          workspace orchestration above storage
  config.py             typed TOML schema
  config_io.py          config load/save
  storage/              SQLite, migrations, records, FTS, costs
  connectors/           files and JSONL threads
  chunking/             markdown/text and code
  ingest/               sync pipeline and bursts
  distill/              cards (heuristic and optional LLM)
  lanes/                retrieval (lexical FTS lanes)
  providers/            optional chat HTTP client and FakeLLM
  tokenize.py
  prompts/              card.v1 and later prompt files
tests/                  unit, integration, e2e, fixtures
openspec/               specs, changes, archive
docs/                   spec, decisions, evidence, PROGRESS.md
scripts/                module-size gate, wheel smoke
```

Storage and retrieval stay separate. `lodestone.storage` owns the SQLite file,
forward-only migrations, records and FTS writes. Retrieval (`lodestone.lanes`,
and later fusion/rerank) reads ranked ids from those indexes and must not be
imported by storage. Connectors and chunkers feed ingest; ingest writes through
storage. The CLI sits above workspace; workspace sits above storage; nothing
imports `lodestone.cli`.

Import-linter contracts in `importlinter.ini` are the enforceable graph:

- Layers: `cli` → `workspace` → `storage` → `config`
- Lexical graph: `cli` → `workspace` → `ingest | lanes` → `distill` →
  `providers | chunking | connectors | storage` → `config_io` →
  `config | tokenize`

Do not add upward imports. New packages must land on the matching layer and
extend the contracts instead of bypassing them.

## Setup and commands

Python 3.11+ with SQLite FTS5. From a virtualenv:

```sh
pip install -e '.[dev,vec]'
pre-commit install
ruff check .
ruff format --check .
mypy --strict src
lint-imports --config importlinter.ini
python scripts/check_modules.py
pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=80
python -m build
```

CI runs the same lint, type, import, module-size, coverage, OpenSpec, license
and wheel jobs. Coverage is also gated by `[tool.coverage.report] fail_under = 80`
in `pyproject.toml`. Default pytest excludes `@pytest.mark.network` and
`@pytest.mark.perf`. Install OpenSpec with
`npm i -g @fission-ai/openspec@latest` when editing specs.

## OpenSpec workflow

Use real OpenSpec (`@fission-ai/openspec`). Change names are feature-shaped
verb-noun slugs (for example `add-threads-and-bursts`), never numbered delivery
labels.

1. **Propose** — `/opsx-propose` or `openspec new change NAME` with proposal,
   design, tasks and requirement spec deltas.
2. **Apply** — `/opsx-apply` implements the change. Keep planning artifacts and
   code in step.
3. **Validate** — `openspec validate NAME --strict` and
   `openspec validate --all --strict` must pass before a PR is ready.
4. **Archive after merge** — archive only once the change is on `main`. Commit
   the archive directly on `main`. Do not rewrite history.

## Conventions

- Conventional Commits; small, focused commits.
- Python modules in `src/`, `tests/` and `scripts/` stay at or below 500 lines
  and start with `# SPDX-License-Identifier: Apache-2.0`.
- Never edit an existing file in `src/lodestone/storage/migrations/`. Add a new
  `NNNN_name.sql` and bump the schema version.
- No network and no paid APIs in the default test run. Network tests are
  opt-in (`pytest -m network`).
- Name tests with the requirement ID (`test_fr_001_...`).
- Never weaken, skip or delete a CI check.
- Paste command output in `docs/evidence/<feature>.md` (feature slug, not a
  numbered delivery label).
- Add a row to `docs/PROGRESS.md` per feature, with PR, CI URL, requirement IDs
  and status.
- Use feature-named branches (`feat/<slug>`, `chore/<slug>`, `docs/<slug>`).
- Merge to `main` with `git merge --no-ff`. Do not rewrite history.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the short setup list and
[docs/spec/02-architecture.md](docs/spec/02-architecture.md) for the full
component map.
