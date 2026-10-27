# Security

Report vulnerabilities privately through this repository's GitHub Security
Advisories (Security → Report a vulnerability). Do not post secrets publicly.

| Version | Support |
|---|---|
| Current main / 0.1.0.dev0 | Development security fixes |

Areas of interest include secret exposure, path jail (files connector),
prompt injection in retrieved text, SQLite integrity, and MCP remaining
read-only. API keys belong in the environment, never in TOML.
