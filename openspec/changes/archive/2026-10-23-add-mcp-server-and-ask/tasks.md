# Tasks

## 1. MCP server

- [x] 1.1 Pin `mcp>=2,<3`, add ADR `docs/decisions/0007-mcp-sdk-v2.md`, and
      extend import-linter so `mcp_server` sits under `cli` and above `sdk`.
- [x] 1.2 Implement `lodestone.mcp_server` with six read-only tools, SQLite
      `mode=ro`, and no query-log writes; verify
      `test_fr_052_mcp_tools_validate_against_schema` and
      `test_fr_052_readonly_db_rejects_writes`.
- [x] 1.3 Expose who-knows and recent as MCP tools; verify
      `test_fr_043_mcp_who_knows_returns_people` and
      `test_fr_044_mcp_recent_returns_evidence`.
- [x] 1.4 Offline socket-blocking test; verify
      `test_fr_052_offline_mcp_makes_no_network`.

## 2. Ask pipeline

- [x] 2.1 Implement planner catalog, allow-list validation, and deterministic
      fallback; verify `test_fr_054_planner_fallback_on_malformed_plan`.
- [x] 2.2 Implement executor, evidence normalisation, synthesis, and citation
      validator; verify `test_fr_053_citations_only_retrieved_ids` and
      `test_fr_053_empty_evidence_refuses`.
- [x] 2.3 Implement sufficiency loop bounded by `ask.max_rounds`; verify
      `test_fr_055_adversarial_sufficiency_terminates`.
- [x] 2.4 Wire `Lodestone.ask` and CLI `lodestone ask` / `lodestone mcp`;
      verify `test_fr_051_ask_and_mcp_commands`.

## 3. Injection, docs and gates

- [x] 3.1 Add ten injection payloads under `tests/fixtures/` and treat them as
      data; verify `test_fr_056_injection_payloads_do_not_alter_tools`.
- [x] 3.2 Add `docs/mcp.md` with Claude Code and Cursor snippets.
- [x] 3.3 Raise coverage to 85% in pyproject, CI, and contributor docs; verify
      pytest `--cov-fail-under=85`.
- [x] 3.4 Run `openspec validate add-mcp-server-and-ask --strict`, ruff, mypy
      --strict, import-linter, module-size gate, and pytest.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
