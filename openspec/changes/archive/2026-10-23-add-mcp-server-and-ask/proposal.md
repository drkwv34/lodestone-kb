# Proposal

## Why

Fused search, who-knows, recent, and the typed SDK already exist, but coding
agents still cannot call those primitives over MCP, and `lodestone ask` is a
stub. This change adds the read-only MCP server and the cited ask pipeline so
retrieval stays LLM-free while orchestration is optional.

## What Changes

- Add a stdio MCP server (`mcp_server.py`) with six read-only tools: `search`,
  `grep`, `get_record`, `list_sources`, `who_knows`, and `recent`. Open the
  index with SQLite `mode=ro`. Pin the official `mcp` Python SDK to a 2.x
  range (`MCPServer` replaces architecture's `FastMCP`) and record the
  deviation in a new ADR.
- Implement `ask/{planner,executor,sufficiency,synthesis}.py` on the existing
  search pipeline and provider layer: planner tool JSON, parallel executor,
  evidence normalisation, numbered citations, empty-evidence refusal, and a
  sufficiency loop bounded by `ask.max_rounds`.
- Add CLI `lodestone mcp` and `lodestone ask`; wire SDK `Lodestone.ask`.
- Add a 10-payload injection fixture corpus and `docs/mcp.md` with Claude Code
  and Cursor config snippets.
- Raise the NFR-012 coverage gate from 80% to 85% with real tests.

**Not in this change:** bench commands, write tools on MCP, schema migrations.

## Capabilities

### New Capabilities

- `mcp-ask`: read-only MCP stdio tools over existing retrieval, plus the ask
  planner/executor/sufficiency/synthesis pipeline with citation validation and
  untrusted-content handling.

### Modified Capabilities

- `repository-gates`: NFR-012 coverage gate ramps to at least 85% from this
  feature on (CI `--cov-fail-under` and `fail_under`).

## Impact

New `lodestone.mcp_server` and `lodestone.ask` packages; CLI commands; SDK
`ask`; FakeLLM planner/sufficiency/synthesis rules; `mcp>=2,<3` dependency;
import-linter layers; docs and evidence. Search without MCP/ask is unchanged.
No paid APIs and no network in tests. Coverage gate becomes 85%.
