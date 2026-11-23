# Spec Delta

## MODIFIED Requirements

### Requirement: FR-052 read-only MCP server
The system SHALL implement "FR-052": an MCP stdio server using the official
`mcp` Python SDK that exposes tools `search`, `grep`, `get_record`,
`list_sources`, `who_knows`, and `recent`. Every tool is LLM-free except
`search(rerank=true)`. Inputs are JSON-schema'd. `search` and `recent` output
`evidence.v1` hits. The process opens the SQLite database with `mode=ro` and
exposes no write tools. With `--offline`, the process makes no network
connections.

#### Scenario: Client lists and calls six tools
- **WHEN** an MCP client connects in-process or over stdio
- **THEN** `tools/list` returns exactly those six tools and each `tools/call`
  succeeds with a result that matches the documented output shape, and search
  or recent hits validate against `evidence.v1`

#### Scenario: Offline MCP makes no sockets
- **WHEN** the server is started with `--offline` and sockets are patched to
  raise
- **THEN** listing tools and calling `search` complete without opening a
  network connection

#### Scenario: Read-only database
- **WHEN** a write is attempted through the MCP database connection
- **THEN** SQLite rejects the write

#### Scenario: Search with explain true
- **WHEN** an MCP client calls `search` with `explain` true
- **THEN** the call succeeds and each hit validates as `evidence.v1` including
  a nested `explain.lanes` object
