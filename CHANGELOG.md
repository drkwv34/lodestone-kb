# Changelog

All notable changes are documented in this file.

## 0.1.0.dev0

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
