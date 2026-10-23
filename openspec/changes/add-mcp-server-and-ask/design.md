# Design

## Context

See proposal.md. Retrieval (fusion, grep, who-knows, recent), the typed SDK,
CLI, FakeLLM, and query log already exist. `Lodestone.ask` raises
`NotImplementedError`. Architecture 3.10 still names `FastMCP`; PyPI `mcp`
2.3.0 renamed that class to `MCPServer`. Import-linter currently has
`cli → sdk → workspace → experts → fusion → rerank → …`. `cli.py` is 499
lines and `workspace.py` is 498. Existing migrations are immutable.

## Goals / Non-Goals

**Goals:**
- Six read-only MCP tools over the existing SDK/workspace retrieval, with the
  index opened `mode=ro`.
- Ask pipeline modules that call those same primitives, with planner fallback,
  citation validation, bounded sufficiency, and injection-safe prompts.
- CLI `mcp` / `ask` without exceeding the 500-line module gate.
- Coverage gate 85% with real tests; ADR for the MCP SDK rename.

**Non-Goals:**
- Bench commands, write MCP tools, schema bump, rewriting fusion/lanes/storage.

## Decisions

1. **MCP SDK 2.x (`MCPServer`), not `FastMCP`.** Pin `mcp>=2,<3`. Import
   `from mcp.server import MCPServer`. In-process tests use
   `async with Client(server) as client`. Stdio uses `server.run(transport="stdio")`.
   Alternative: stay on 1.x to match the architecture name; rejected because
   `pip install mcp` installs 2.x and the v1 FastMCP module is gone. Record this
   in `docs/decisions/0007-mcp-sdk-v2.md`.

2. **MCP sits above SDK; ask sits with workspace.** Import-linter:
   `cli → mcp_server → sdk → workspace | ask → …`. CLI imports `mcp_server`
   to run stdio. Ask does not import SDK (callables/config injected from
   `Lodestone.ask`) so the graph stays downward. Alternative: MCP calling
   fusion directly; rejected because it would duplicate workspace filters.

3. **Read-only connection and no query-log writes on the MCP path.** MCP opens
   SQLite with `mode=ro` (helper on `storage.db`). Tools reuse SDK/workspace
   reads inside a `skip_query_log` context so MCP cannot INSERT `query_log`.
   A unit test issues `INSERT` on that connection and expects
   `sqlite3.OperationalError`. Alternative: a separate read replica; rejected
   as unnecessary for a single local file.

4. **Planner allow-list and deterministic fallback.** Planner prompt includes
   "planner" / "tool calls" so FakeLLM `default_plan` applies. Question is the
   last line so indexed injection text in the catalog cannot change the
   rule-based plan. Validate JSON to at most 4 calls in
   `{search, grep, who_knows, recent}`; drop unknown tools; empty/invalid →
   `search` plus `grep` when `IDENTIFIER` matches. Executor fans out with
   `asyncio.gather` + `asyncio.to_thread`.

5. **Evidence ids `E1..En` and citation validator.** Dedupe by record id,
   keep best score, assign sequential labels. Synthesis wraps each item in
   `<evidence id="E1" …>` with an instruction-hierarchy note that retrieved
   text is untrusted data. Accept citations `[E1]` or `[1]`; strip ids that
   were not retrieved. Empty packet → `insufficient_evidence=true` and no
   synthesis call.

6. **Sufficiency after a draft, bounded by `max_rounds`.** Follow FR-055
   (after synthesis-draft) rather than architecture 2.3 (before synthesis).
   Default `ask.max_rounds=3` so at most two follow-up tool rounds. A
   `NEED:<query>` reply becomes one `search` call. An adversarial FakeLLM that
   always returns NEED still stops at `max_rounds` and returns the last draft
   (or refusal if still empty).

7. **CLI room: extract tiny helpers, keep command bodies.** Move
   `configuration` / `fail` / `Caught` into `lodestone/cli_support.py` so
   `cli.py` can register `mcp` and `ask` without crossing 500 lines. Ask and
   MCP option parsing stay in `cli.py` as thin Typer commands.

8. **Coverage 85%.** Update `pyproject.toml` `fail_under`, CI
   `--cov-fail-under`, CONTRIBUTING/AGENTS, and the repository-gates spec.
   Reach the gate with MCP/ask tests, never by omitting modules.

## Risks / Trade-offs

- [MCP 2.x vs architecture FastMCP] → ADR-0007; tests use `MCPServer` +
  `Client(server)`.
- [cli.py / workspace.py line budget] → extract support helpers; skip query
  log via contextvar instead of extra kwargs on every function.
- [Injection via catalog top-terms] → rule-based planner keys off the last
  prompt line (the user question); retrieved text only appears inside
  evidence tags at synthesis time.
- [Query log vs read-only MCP] → skip log writes on the MCP path; ask/CLI
  still log.

## Migration Plan

No schema bump. After upgrade, existing search/CLI behaviour is unchanged.
`lodestone mcp` and `lodestone ask` are additive. Rollback: do not run those
commands; pin can stay because `mcp>=1.2` already resolved to 2.x.
