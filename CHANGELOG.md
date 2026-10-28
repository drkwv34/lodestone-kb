# Changelog

All notable changes are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
after the first `0.1.0` release. See [docs/RELEASE.md](docs/RELEASE.md).

## [0.1.0rc1] - 2026-10-28

Release candidate. Not published to PyPI.

### Added

- `lodestone bench import beir:scifact` converts a local BEIR-format corpus,
  queries, and qrels into markdown documents plus `evalset.v1` (FR-079).
  Default tests use a tiny fixture; optional public-mirror download verifies
  the published SciFact MD5 and is network-marked.
- Dockerfile for the read-only MCP stdio server (`lodestone mcp --offline`)
  and an Ubuntu CI job that runs `docker build` without pushing an image.
- `lodestone --version` prints the package version (`0.1.0rc1`).
- `docs/RELEASE.md` release checklist and later PyPI cut notes.
- Honest H1–H5 hypothesis table in `docs/benchmarks/FINDINGS.md`.

### Changed

- Package version is `0.1.0rc1` (PEP 440). Git tag for this candidate is
  `v0.1.0-rc1`.

## [0.1.0.dev0]

Pre-release development snapshot. Not published to PyPI.

- Local workspace: `lodestone init`, typed TOML, SQLite FTS5, forward
  migrations
- Files and JSONL thread connectors, structural chunking, bursts, distilled
  cards (heuristic and optional LLM)
- Hybrid search (FTS, rare terms, recency, optional vectors), explain,
  rerank, SDK, CLI
- Read-only MCP stdio server and `lodestone ask`
- Offline RAG-strategy benchmark (`synth`, `run`, `report`, `advise`) with
  resume cache
- Plugin connectors, crash-safe ingest, `doctor --deep`
- User guides, offline quickstart script, docs link check, and verified
  wheel + sdist packaging
