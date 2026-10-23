# Lodestone

> Embedding-optional knowledge engine: distilled cards, explainable hybrid search,
> an MCP server, and a benchmark that tells you which RAG strategy your corpus needs.

[![CI](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml/badge.svg)](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
![Python 3.11–3.13](https://img.shields.io/badge/python-3.11–3.13-blue)

Local Markdown/text, code and JSONL thread ingestion, structural chunking,
distilled cards, lexical search and optional embeddings are available through
`init`, `doctor`, `config show`, `source add/list/remove/sync`, `sync`,
`search`, `grep`, `get`, `who-knows`, `recent`, `ask`, `mcp`, `stats` and
`reindex`. The Python SDK is `Lodestone.open`. See [docs/mcp.md](docs/mcp.md)
for Claude Code and Cursor config. No automatic PyPI publishing is configured.

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
pip install -e '.[vec]'   # sqlite-vec extra is optional; omit [vec] for brute-force only
lodestone init && lodestone doctor
lodestone config show
```

`lodestone init [PATH]` creates `lodestone.toml` and `.lodestone/index.db` and is
idempotent. Existing configuration and records are preserved. Database and source
paths resolve relative to the config file. Use `doctor --config PATH` or
`config show --config PATH` for another workspace. Unknown config keys produce
exit 2 with a field path. Runtime/storage failures produce exit 1.

Register a source, then sync and search:

```sh
lodestone source add wiki --kind files --path tests/fixtures/corpus --exclude 'drafts/**'
lodestone source list
lodestone sync --offline
lodestone search "ERR_MANIFEST_TIMEOUT"
lodestone grep "ERR_MANIFEST_TIMEOUT"
lodestone who-knows "manifest"
lodestone recent --limit 5
lodestone ask "Why does restore stall?" --provider fake --offline
lodestone mcp --offline
lodestone stats
lodestone search "ERR_MANIFEST_TIMEOUT" --lane vec_card --offline --explain --json
lodestone reindex --lanes vec --offline
lodestone search '"manifest load"' --source wiki --kind section --json
lodestone source sync wiki --prune
```

Typed SDK (this snippet is a doctest; no network):

```python
>>> from pathlib import Path
>>> from tempfile import TemporaryDirectory
>>> from lodestone import Lodestone
>>> with TemporaryDirectory() as tmp:
...     kb = Lodestone.open(Path(tmp), offline=True)
...     _ = kb.sync()
...     result = kb.search("nothing-at-all")
...     isinstance(result.hits, list)
True

```

Markdown/text files retain a `doc` parent plus ordered `section` children; code
files retain a `code_file` parent with signature outline and ordered `code`
children. Supported code kinds: Python, JavaScript, TypeScript, Go, Java, C, C++
and Rust. Heading paths become section titles. Chunks target 400 tokens and never
exceed 800 (configurable; one token defaults to four characters). Fenced code stays
intact unless it exceeds the maximum. Code uses coarse regex symbol/block
boundaries with a bounded text fallback.

Nested `.gitignore` rules apply and binaries/oversize files are skipped with logged
reasons. Unchanged normalised content produces zero record writes. Deleted files
are tombstoned and hidden from search; `sync --prune` purges them. Skipped files
retain their previous indexed version until readable again or explicitly removed.
`source remove wiki` removes the source and its records, FTS, embeddings and term
contributions. Source mutations re-emit valid TOML values and replace the file
atomically; formatting and comments are not retained.

Projects are explicit source sets. `source add` includes a source in the selected
project. Thread JSONL sources use `--kind threads`. Convert a Slack export with
`examples/slack_export_to_jsonl.py`, then sync. Qualifying same-author bursts are
stored as `kind=burst` children. Edit TOML to create projects and share sources:

```toml
[[projects]]
name = "default"
sources = ["wiki"]
[[projects]]
name = "reference"
sources = ["wiki"]
```

`search`, `sync` and `source` commands accept `--project reference`; the default
comes from `workspace.default_project`. Explicit empty projects select no sources.
When `projects` is omitted, a `default` project includes all configured sources.
Repeatable `--source` filters intersect project membership, and `--kind` filters
record types. Search defaults to `fts_raw`; `--lane fts_rare` selects rare terms
and `--lane vec_card` / `vec_chunk` use stored embeddings. Embeddings are off
until `embed.provider` is `hash` or `openai_compat`, or until `--offline` /
`offline = true` swaps in the 256-d hash embedder (deterministic, **not
semantic**). Disabled or mismatched vec lanes return no hits and a notice in
`result.notices`. `reindex --lanes vec` rebuilds embeddings from stored text
without contacting sources. Default IDF >=4 can select no terms on tiny
corpora; `[retrieval] rare_df_ratio` provides a corpus-relative alternative.
Search opens the database read-only; `init` and `sync` apply forward schema
migrations. sqlite-vec is used when the `[vec]` extra is installed, otherwise
exact brute-force cosine (stdlib array, numpy if present).

## Features and comparison (roadmap)

| Capability | Available | Planned |
|---|---|---|
| Typed TOML, schema migrations, local diagnostics | Available | Expanded diagnostics |
| Lexical indexing and search | Available: raw/rare lanes, fused hybrid search, optional LLM rerank | — |
| Optional embeddings and vec lanes | Available: hash/openai_compat, brute-force and sqlite-vec, vec_card/vec_chunk, `--offline`, `reindex --lanes vec` | — |
| Thread cards, burst records, recency | Available: JSONL threads, cards, bursts, recency decay | — |
| Typed SDK and CLI | Available: `Lodestone` facade, grep/who-knows/recent/stats | MCP, ask, bench |
| Read-only MCP for coding agents | Planned | MCP server |
| Corpus-specific strategy benchmark | Planned | Strategy evaluation |
| Tree reasoning over long documents (PageIndex style) | Out of scope | Not in MVP |

## MCP

The read-only server and client configuration are planned.

## Benchmark

`lodestone bench synth|run|report|advise` is planned. The hash embedder is
deterministic and **not semantic**. Synthetic results will carry leakage and
small-corpus caveats.

## Privacy and data flow

The available commands create or read local TOML and SQLite files only. No
telemetry, provider requests or paid APIs are used. Optional provider credentials
are named via `api_key_env`; literal keys are rejected. `config show` redacts
fields containing key/token/secret. `LODESTONE_LLM_API_KEY` and
`LODESTONE_EMBED_API_KEY` override configured environment references at runtime
without entering TOML or config output. Keep workspace files out of version control.
`--offline` blocks remote chat and embedding clients with `OfflineError` and
uses the hash embedder plus heuristic cards. Doctor currently probes Python,
SQLite, FTS5 and schema; sqlite-vec/provider/deep checks are deferred to the
later diagnostics delivery.

## Roadmap and scope

See [the delivery plan](docs/spec/03-delivery-plan.md), [progress](docs/PROGRESS.md)
and [chunking and source evidence](docs/evidence/chunkers-sources.md). The MVP
targets a single local user;
live Slack ingestion, distributed storage and a web UI are out of scope.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CI uses no paid APIs and requires strict
typing, Ruff, import boundaries, modules <=500 lines, dependency license checks
and at least 80% line coverage.

Licensed under [Apache-2.0](LICENSE); see [NOTICE](NOTICE).
