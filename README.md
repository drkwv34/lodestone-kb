# Lodestone

> Embedding-optional knowledge engine: distilled cards, explainable hybrid search,
> an MCP server, and a benchmark that tells you which RAG strategy your corpus needs.

[![CI](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml/badge.svg)](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
![Python 3.11–3.13](https://img.shields.io/badge/python-3.11–3.13-blue)

Day 2 of 14: local md/txt/rst ingestion and lexical search. Available commands
are `init`, `doctor`, `config show`, `sync` and `search`. Further engine features
remain planned.
No automatic PyPI publishing is configured.

## Why

Classic chunk-and-embed RAG can lose exact identifiers, thread context and
freshness. Lodestone aims to distil conversations into question-shaped cards,
combine lexical signals with optional vectors, explain rankings, and benchmark
the strategies on your data. Inspired by Cerebras' "How we built our knowledge
base" (2026). Independent project, not affiliated with Cerebras.

## Quickstart (offline, from source)

Python 3.11+ with SQLite >=3.38 and FTS5 is required. Package installation needs
network access; all available commands run locally without API credentials.

```sh
git clone https://github.com/drkwv34/lodestone-kb.git
cd lodestone-kb
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
lodestone init && lodestone doctor
lodestone config show
```

`lodestone init [PATH]` creates `lodestone.toml` and `.lodestone/index.db` and is
idempotent. Existing configuration and records are preserved. Database and source
paths resolve relative to the config file. Use `doctor --config PATH` or
`config show --config PATH` for another workspace. Unknown config keys produce
exit 2 with a field path. Runtime/storage failures produce exit 1.

Add a files source to `lodestone.toml`, then sync and search:

```toml
[[sources]]
name = "wiki"
kind = "files"
path = "tests/fixtures/corpus"
include = ["**/*.md", "**/*.txt", "**/*.rst"]
exclude = ["drafts/**"]
max_file_bytes = 1048576
```

```sh
lodestone sync
lodestone search "ERR_MANIFEST_TIMEOUT"
lodestone search '"manifest load"' --source wiki --kind doc --json
lodestone search 'manif*' --limit 5
```

Each file becomes one `doc`; nested `.gitignore` rules apply, binaries/oversize
files are skipped with logged reasons, and unchanged normalised content produces
zero record writes. `--source` and `--kind` are repeatable. Search defaults to
`fts_raw`; `--lane fts_rare` selects only rare query terms. With default IDF >=4,
tiny corpora can have no qualifying terms; set `[retrieval] rare_df_ratio = 0.02`
for a corpus-relative threshold. Chunks, pruning, projects and fusion are scheduled
for later days. Search opens the database read-only; `init` or `sync` applies
forward schema migrations.

## Features and comparison (roadmap)

| Capability | Day 2 | Planned |
|---|---|---|
| Typed TOML, schema migrations, local diagnostics | Available | Expanded diagnostics |
| Lexical indexing and search | Available: raw/rare lanes | Hybrid fusion Day 7 |
| Thread cards, burst records, recency | Planned | Days 4–7 |
| Read-only MCP for coding agents | Planned | Day 9 |
| Corpus-specific strategy benchmark | Planned | Days 10–12 |
| Tree reasoning over long documents (PageIndex style) | Out of scope | Not in MVP |

## MCP

The server and Claude Code / Cursor configuration are scheduled for Day 9.

## Benchmark

`lodestone bench synth|run|report|advise` is scheduled for Days 10–12. The planned
hash embedder is deterministic and **not semantic**. Synthetic results will carry
leakage and small-corpus caveats.

## Privacy and data flow

The available commands create or read local TOML and SQLite files only. No
telemetry, provider requests or paid APIs are used. Optional provider credentials
are named via `api_key_env`; literal keys are rejected. `config show` redacts
fields containing key/token/secret. Keep workspace files out of version control.
Doctor currently probes Python, SQLite, FTS5 and schema; sqlite-vec/provider/deep
checks are deferred to the later diagnostics delivery.

## Roadmap and scope

See [the delivery plan](docs/spec/03-delivery-plan.md), [progress](docs/PROGRESS.md)
and [Day 2 evidence](docs/evidence/day-02.md). The MVP targets a single local user;
live Slack ingestion, distributed storage and a web UI are out of scope.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CI uses no paid APIs and requires strict
typing, Ruff, import boundaries, modules <=500 lines, dependency license checks
and at least 70% line coverage on Days 1–3 (80% from Day 4, 85% from Day 9).

Licensed under [Apache-2.0](LICENSE); see [NOTICE](NOTICE).
