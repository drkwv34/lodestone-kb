# MCP server

Lodestone exposes LLM-free retrieval as a read-only MCP stdio server. The
process opens the workspace SQLite file with `mode=ro` and registers six
tools: `search`, `grep`, `get_record`, `list_sources`, `who_knows`, and
`recent`. Only `search(rerank=true)` may call a chat model.

Start it from a workspace directory:

```sh
lodestone mcp --config lodestone.toml --offline
```

`--offline` replaces remote providers and is the safe default in CI and
untrusted-host setups. The server does not ingest or mutate records; use
`lodestone sync` from the CLI for writes.

## Claude Code

Add a stdio server in Claude Code's MCP settings (JSON). Adjust the command
if `lodestone` is not on `PATH`:

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

## Cursor

Cursor MCP config (`.cursor/mcp.json` or the MCP settings UI):

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

Point `--config` at a workspace that already has a synced index. More
context: [concepts.md](concepts.md), [privacy.md](privacy.md).
