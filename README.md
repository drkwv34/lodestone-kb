# Lodestone

> Embedding-optional knowledge engine: distilled cards, explainable hybrid search, an MCP server, and a benchmark that tells you which RAG strategy your corpus actually needs.

[![CI](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml/badge.svg)](https://github.com/drkwv34/lodestone-kb/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
![Python 3.11–3.13](https://img.shields.io/badge/python-3.11–3.13-blue)

## Why

Classic RAG is chunk + embed + top-k. It loses exact tokens, thread context and
freshness, and nobody tells you if it was worth it.

Lodestone distils threads and docs into question-shaped *cards*, searches with
several cheap signals (exact tokens, rare terms, recency, optional vectors),
shows *why* each hit ranked, and ships `lodestone bench` to compare classic RAG,
hybrid, cards, agentic grep and full-context **on your data**.

Inspired by Cerebras' "How we built our knowledge base" (2026). Independent
project, not affiliated with Cerebras.

## Quickstart (offline, 2 minutes)

Python 3.11+ with SQLite FTS5. The intended install is `pip install lodestone-kb`
once a release is published. This tree is `0.1.0.dev0` and is **not** on PyPI
yet; install from source:

```sh
git clone https://github.com/drkwv34/lodestone-kb.git
cd lodestone-kb
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[vec]'   # sqlite-vec extra is optional
```

Then, in any directory:

```sh
lodestone init && lodestone source add docs --kind files --path ./docs
lodestone sync --offline && lodestone search "ERR_MANIFEST_TIMEOUT" --explain
```

`examples/quickstart.sh` runs that walkthrough against a temp workspace and is
executed in CI. See [docs/quickstart.md](docs/quickstart.md).

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

## Features / How it compares

| Capability | qmd | SQLite-hybrid MCP servers | PageIndex | Lodestone |
|---|---|---|---|---|
| FTS5 + RRF + MCP | yes | yes | no | yes |
| Distilled question-shaped cards for threads | no | no | no | **yes** |
| Burst records with rarity/engagement gate | no | no | no | **yes** |
| Age decay as a first-class signal | no | metadata only | no | **yes** |
| Works with zero embeddings / zero LLM | partial | partial | no | **yes (`--offline` is tested)** |
| Cross-paradigm benchmark with cost, latency, CIs | no | no | vendor benches | **yes** |
| Recommendation verdict | no | no | no | **yes (`bench advise`)** |

Shipped CLI: `init`, `doctor`, `config show`, `source add/list/remove/sync`,
`sync`, `search`, `grep`, `get`, `who-knows`, `recent`, `ask`, `mcp`, `stats`,
`cost`, `reindex`, `bench synth|generate|run|report|advise`. Python SDK:
`Lodestone.open`. Read-only MCP stdio server. Optional OpenAI-compatible chat
and embeddings. Hash embedder is deterministic and **not semantic**.

Guides: [concepts](docs/concepts.md) · [connectors](docs/connectors.md) ·
[MCP](docs/mcp.md) · [bench](docs/bench.md) · [privacy](docs/privacy.md) ·
[FAQ](docs/faq.md) · [provider presets](docs/providers.md)

## MCP (Claude Code / Cursor)

```json
{
  "mcpServers": {
    "lodestone": {
      "command": "lodestone",
      "args": ["mcp", "--config", "/absolute/path/to/lodestone.toml", "--offline"]
    }
  }
}
```

The server opens SQLite with `mode=ro`. Details: [docs/mcp.md](docs/mcp.md).

## Benchmark

```sh
lodestone bench synth --seed 42 --threads 60 --out ./bench/synth
lodestone bench run --corpus ./bench/synth --out ./bench/run --offline
lodestone bench report ./bench/run
lodestone bench advise ./bench/run
```

The hash embedder is **not semantic**. Synthetic offline results and labelled
instructions for real-embedder runs live in
[docs/benchmarks/](docs/benchmarks/FINDINGS.md). Interrupted runs resume from a
per-question cache (zero duplicate LLM calls).

## Privacy and data flow

Default operation is local files and SQLite. No telemetry. API keys come from
the environment (`api_key_env`), never from TOML. `--offline` blocks remote
chat and embedding clients. See [docs/privacy.md](docs/privacy.md).

## Roadmap / Out of scope

See [the delivery plan](docs/spec/03-delivery-plan.md) and
[progress](docs/PROGRESS.md). Live Slack ingestion, distributed storage, a web
UI, and automatic PyPI publishing are out of scope. A tag-triggered GitHub
Release builds wheel + sdist artifacts; nothing is uploaded to PyPI
automatically.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[compatibility](docs/compatibility.md). Public APIs follow semver;
deprecations warn for one minor version. Modules stay at or below 500 lines.
CI uses no paid APIs.

Licensed under [Apache-2.0](LICENSE); see [NOTICE](NOTICE).
