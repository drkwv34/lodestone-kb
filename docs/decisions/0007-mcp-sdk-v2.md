# MCP Python SDK v2 (`MCPServer`)

Architecture 3.10 names the official Python MCP class `FastMCP` from
`mcp.server.fastmcp`. The current PyPI release is `mcp` 2.3.0. In v2 that
class was renamed to `MCPServer` (`from mcp.server import MCPServer`); the
`mcp.server.fastmcp` module is gone. `pip install mcp` installs 2.x.

Lodestone pins `mcp>=2,<3` and implements the stdio server with `MCPServer`.
In-process tests use `mcp.client.Client(server)`. Tool decorator APIs
(`@server.tool()`, JSON Schema from type hints, `server.run(transport="stdio")`)
match the architecture's intended FastMCP usage aside from the rename.

No protocol behaviour was dropped: six read-only tools, evidence.v1 hits, and
SQLite `mode=ro` are unchanged from architecture 3.10.
