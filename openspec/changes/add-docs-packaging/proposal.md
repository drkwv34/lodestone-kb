# Proposal

## Why

Retrieval, MCP, ask, and the offline benchmark already ship, but the public
README still describes MCP and bench as planned, user guides are incomplete,
and the first-search walkthrough is not executed in CI. Docs and packaging
close that gap so a new user can install a verified wheel, search offline, and
read honest guides without inventing benchmark numbers.

## What Changes

- Rebuild README from the repository bootstrap skeleton, accurate to shipped
  commands (init, source, sync, search, MCP, ask, bench).
- Add user guides: quickstart, concepts, connectors, mcp, bench, privacy, faq.
- Add `examples/quickstart.sh` and run it offline in CI (NFR-013).
- Add a CI link check over README and user docs; skip or mock external URLs
  while requiring internal links to resolve (NFR-016).
- Document public-API semver and one-minor deprecation policy; keep the
  existing module-size lint as the NFR-014 gate.
- Verify wheel + sdist by installing `dist/*.whl` into a clean venv and
  running the CLI.
- Record synthetic offline bench results that were actually run in
  `docs/benchmarks/`; label real-embedder runs `status: not run - needs keys`
  in `FINDINGS.md`. Never invent numbers.
- Keep FR-064 config-schema validation of Cerebras, OpenAI, and Ollama
  snippets. Cite the existing FR-078 kill-and-resume test; do not reimplement
  resume cache.
- Add a tag-triggered release workflow that builds artifacts and a draft
  GitHub release with no PyPI publish step.

## Capabilities

### New Capabilities

- `docs-packaging`: user guides, offline quickstart, docs link check, semver
  and deprecation policy, verified wheel install, and labelled benchmark
  findings.

### Modified Capabilities

- None. FR-064 remains under `rerank-sdk-cli`. FR-078 remains under
  `bench-agentic-advise`. Module-size lint remains under `repository-gates`
  (NFR-012); this change documents the NFR-014 semver policy alongside that
  lint.

## Impact

README, `docs/*.md`, `docs/benchmarks/`, `examples/quickstart.sh`, CI jobs
(link check, quickstart, clean-venv wheel), `scripts/check_links.py`,
packaging smoke, `CONTRIBUTING.md`, `CHANGELOG.md`, and
`.github/workflows/release.yml`. No storage migrations, no retrieval
rewrites, no paid APIs, no network in default tests.
