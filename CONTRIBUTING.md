# Contributing

See [AGENTS.md](AGENTS.md) for layout, architecture boundaries, exact commands,
OpenSpec workflow and project conventions. Public API stability is in
[docs/compatibility.md](docs/compatibility.md): semver after `0.1.0`,
deprecations warn for one minor version, modules stay at or below 500 lines.

Use Python 3.11+ and a virtual environment:

```sh
pip install -e '.[dev,vec]'
pre-commit install
ruff check .
ruff format --check .
mypy --strict src
lint-imports --config importlinter.ini
python scripts/check_modules.py
python scripts/check_links.py
pytest -q --cov=src/lodestone --cov-report=term-missing --cov-fail-under=85
python -m build
```

Name tests with the requirement ID (`test_fr_001_...`). No paid APIs in tests.
Network tests are opt-in (`pytest -m network`). Performance tests are opt-in
(`pytest -m perf`). Keep modules at or below 500 lines and use SPDX Apache-2.0
headers. Run the CI dependency license command before changing dependencies.
See [the code of conduct](CODE_OF_CONDUCT.md).

Install real OpenSpec (`npm i -g @fission-ai/openspec@latest`), initialise with
`openspec init`, and create a change with `openspec new change NAME`. Supply a
proposal, design, tasks and requirement spec deltas. Run
`openspec validate NAME --strict` and `openspec validate --all --strict`.
After a green PR, merge locally using `git merge --no-ff`; archive only after
merge on main and commit the archive directly. Do not rewrite history.

Use small Conventional Commits with the configured owner identity and no
co-author trailers. Paste actual command outputs in feature evidence and the PR.

To add a connector, implement `discover(config)` yielding `ext_id`,
`kind_hint`, `text`, `metadata`, and `updated_at`, and register the class on
the `lodestone.connectors` entry-point group. The entry name is the source
`kind`. See [docs/connectors.md](docs/connectors.md) and
[examples/plugin_demo/](examples/plugin_demo/).
