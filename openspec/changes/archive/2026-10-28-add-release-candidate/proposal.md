# Proposal

## Why

The MVP is on `main` and needs a release-candidate cut: a BEIR adapter so
external IR corpora can feed `lodestone bench`, an MCP container image, and
packaging polish (version, changelog, release checklist, honest hypothesis
status) so `v0.1.0-rc1` can be tagged without publishing to PyPI.

## What Changes

- Add `lodestone bench import beir:scifact` that converts a BEIR-format
  corpus, queries, and qrels into a Lodestone files corpus plus
  `evalset.v1`. Default tests use a tiny local fixture (no downloads).
  Optional download from the public BEIR mirror verifies a pinned SHA-256
  and is marked `@pytest.mark.network`.
- Add a Dockerfile (and `.dockerignore`) for the read-only MCP server, plus
  a CI job that runs `docker build` on Ubuntu only (no image push).
- Bump the package to `0.1.0rc1`, expose matching `lodestone --version`,
  write Keep a Changelog section `0.1.0rc1`, and add `docs/RELEASE.md`
  (how to cut `v0.1.0` later; no PyPI publish in this change).
- Record an honest H1–H5 table in `docs/benchmarks/FINDINGS.md` from
  committed numbers only; keep `status: not run - needs keys` for the
  real-embedder run.
- Publish a requirements status table (every FR/NFR, M/S/C, shipped /
  partial / not shipped, proving tests). All M requirements stay green.
- Unfinished Should items are none; remaining Could work besides FR-079
  is deferred in a decision record.

## Capabilities

### New Capabilities

- `beir-adapter`: import BEIR-format datasets (SciFact) into a Lodestone
  bench corpus and evalset, offline-first with checksummed optional
  download.
- `mcp-container`: container image that runs the read-only MCP stdio
  server, built in CI without pushing a registry image.

### Modified Capabilities

- `docs-packaging`: package version `0.1.0rc1`, CLI `--version`, Keep a
  Changelog `0.1.0rc1` section, `docs/RELEASE.md`, and FINDINGS hypothesis
  table H1–H5 (held / not held / not tested) citing only measured or
  already committed numbers.

## Impact

`src/lodestone/bench/` (import command), CLI `--version`, `pyproject.toml`
/ `__version__`, `Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml`
(docker-build job on Ubuntu), `CHANGELOG.md`, `docs/RELEASE.md`,
`docs/benchmarks/FINDINGS.md`, `docs/PROGRESS.md`,
`docs/evidence/release-candidate.md`, `docs/decisions/`. No storage
migrations. No paid APIs. Default tests stay offline.
