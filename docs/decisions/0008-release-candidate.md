# 0008. Release candidate scope

## Status

Accepted.

## Context

SRS section 11 says Could requirements wait until after `v0.1.0` is tagged.
The delivery plan's release-candidate slot lists FR-079 first, then
unfinished Should items, then the MCP Dockerfile and polish.

## Decision

FR-079 is implemented in `0.1.0rc1` because the delivery-plan sequence for
this slot is the more specific instruction. Default tests stay offline and
use a tiny BEIR-format fixture. The public SciFact zip is optional, checksum
verified against the published MD5, and network-marked.

All Must requirements were already green before this slot. All Should
requirements already have named tests; none were unfinished.

## Deferred

- Other Could work besides FR-079 (none other are specified).
- Live SciFact download in CI (`LODESTONE_NETWORK_TESTS=1` only).
- PyPI publish and a non-draft GitHub Release.
- Real-embedder FINDINGS numbers (no provider keys).
- H1–H5 claims that need a real embedder or a decay/`full-context` pairing
  that was not in the committed synth run.
- NFR-018 pip lockfile and Dependabot config (lower bounds in
  `pyproject.toml` remain the pin; default tests still have no network).

## Consequences

Tag `v0.1.0-rc1` on the green archive commit. Do not tag `v0.1.0`. Do not
publish to PyPI from this candidate.
