# Spec Delta

## Purpose

Publish accurate user guides, an offline first-search walkthrough, verified
wheel packaging, and labelled benchmark findings so a local install is usable
without paid APIs.

## ADDED Requirements

### Requirement: NFR-013 offline quickstart
The system SHALL provide `examples/quickstart.sh` that initialises a workspace,
registers a files source, syncs with `--offline`, and searches
`ERR_MANIFEST_TIMEOUT` without network or paid APIs. CI SHALL run the script.

#### Scenario: Quickstart script runs offline
- **WHEN** `examples/quickstart.sh` executes in a temporary directory with
  `lodestone` on PATH and no network
- **THEN** it exits 0 and the search output includes `ERR_MANIFEST_TIMEOUT`

### Requirement: NFR-016 user docs and link check
The repository SHALL contain README plus `docs/quickstart.md`,
`docs/concepts.md`, `docs/connectors.md`, `docs/mcp.md`, `docs/bench.md`,
`docs/privacy.md`, and `docs/faq.md`. CI SHALL check internal links in README
and those pages; external URLs MAY be skipped or mocked.

#### Scenario: Required pages exist and internal links resolve
- **WHEN** the docs link check runs over README and the required user guides
- **THEN** each required page exists and every relative markdown link resolves
  to a file in the repository

### Requirement: NFR-014 semver and module-size policy
Public Python, MCP, and JSON schemas SHALL follow semver. Deprecations SHALL
warn for one minor version before removal. Each Python module under `src/`,
`tests/`, and `scripts/` SHALL stay at or below 500 lines, enforced by the
existing module-size lint.

#### Scenario: Policy documented and modules stay under the cap
- **WHEN** contributors read the compatibility policy and CI runs the
  module-size lint
- **THEN** the policy states semver plus one-minor deprecation warnings, and
  every gated Python module is at most 500 lines

### Requirement: Verified wheel and sdist install
CI SHALL build a wheel and sdist, install `dist/*.whl` into a clean virtual
environment, and run the CLI (`init`, `doctor`, or equivalent smoke).

#### Scenario: Clean venv installs the wheel
- **WHEN** CI builds distributions and installs `dist/*.whl` into a new venv
- **THEN** the `lodestone` CLI runs successfully from that venv

### Requirement: Benchmark findings stay honest
`docs/benchmarks/` SHALL include synthetic offline results that were actually
measured, plus labelled instructions for real-embedder runs. When provider
keys are absent, `docs/benchmarks/FINDINGS.md` SHALL say
`status: not run - needs keys` for the real-embedder run. Numbers SHALL NOT
be invented.

#### Scenario: Real-embedder status is explicit
- **WHEN** `docs/benchmarks/FINDINGS.md` is read and no provider keys were
  available
- **THEN** the real-embedder section contains `status: not run - needs keys`
  and synthetic numbers match a recorded command transcript
