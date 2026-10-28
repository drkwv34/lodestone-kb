# FAQ

## Does Lodestone require embeddings or an LLM?

No. `--offline` (or `offline = true`) uses heuristic cards and a
deterministic hash embedder. Search, grep, MCP (without rerank), and several
bench strategies run with no network.

## Is the hash embedder semantic?

No. It is a 256-d feature hash for tests and offline demos. Bench reports
state "hash embedder is not semantic" when it is used. Use an
OpenAI-compatible embedder for semantic claims.

## Where do API keys go?

Environment variables named by `api_key_env` in TOML. Literal keys in config
are rejected. `config show` redacts secret fields. Runtime overrides:
`LODESTONE_LLM_API_KEY` and `LODESTONE_EMBED_API_KEY`.

## How do I point chat at Cerebras, OpenAI, or Ollama?

Copy a snippet from [providers.md](providers.md). Lodestone speaks
OpenAI-compatible HTTP only (`base_url`, `model`, `api_key_env`). Optional
`json_mode` maps to `response_format: json_object`. There are no
provider-specific clients.

## Can I publish to PyPI from CI?

No. Tag workflow `.github/workflows/release.yml` builds wheel + sdist,
uploads GitHub Actions artifacts, and opens a **draft** GitHub Release. It
does not publish to PyPI.

## How stable is the public API?

Version `0.1.0rc1` is a release candidate, not a PyPI publish. After `0.1.0`, the SDK, MCP tool
schemas, and `*.v1` JSON schemas follow semver. Deprecations warn for one
minor version before removal. See [compatibility.md](compatibility.md).

## Windows?

CI runs a smoke subset on Windows (`pytest tests/e2e -k smoke`). The POSIX
quickstart script is Linux/macOS. PowerShell venv activation:
`.venv\Scripts\Activate.ps1`.
