# Spec Delta

## ADDED Requirements

### Requirement: Package version 0.1.0rc1 and CLI --version
The installed package version SHALL be `0.1.0rc1`. `lodestone --version`
SHALL print that same version string.

#### Scenario: CLI version matches package metadata
- **WHEN** `lodestone --version` runs against an installed wheel or
  editable install
- **THEN** the printed version equals `importlib.metadata.version("lodestone-kb")`
  and both equal `0.1.0rc1`

### Requirement: Changelog and release checklist
`CHANGELOG.md` SHALL follow Keep a Changelog and include a `0.1.0rc1`
section listing shipped work. `docs/RELEASE.md` SHALL describe how to tag
a release candidate, how semver applies after `0.1.0`, and how a later
`v0.1.0` PyPI publish would work. This change SHALL NOT publish to PyPI
or create a GitHub Release.

#### Scenario: Release docs exist without a publish step
- **WHEN** `CHANGELOG.md` and `docs/RELEASE.md` are read
- **THEN** the changelog has a `0.1.0rc1` section and the release guide
  states that PyPI publish is a later maintainer step, not part of this
  candidate

## MODIFIED Requirements

### Requirement: Benchmark findings stay honest
`docs/benchmarks/` SHALL include synthetic offline results that were actually
measured, plus labelled instructions for real-embedder runs. When provider
keys are absent, `docs/benchmarks/FINDINGS.md` SHALL say
`status: not run - needs keys` for the real-embedder run. Numbers SHALL NOT
be invented. FINDINGS SHALL include a hypothesis table H1–H5 with status
held, not held, or not tested, citing only numbers from a run in this
workspace or already committed files.

#### Scenario: Real-embedder status is explicit
- **WHEN** `docs/benchmarks/FINDINGS.md` is read and no provider keys were
  available
- **THEN** the real-embedder section contains `status: not run - needs keys`
  and synthetic numbers match a recorded command transcript

#### Scenario: Hypotheses H1–H5 are labelled
- **WHEN** `docs/benchmarks/FINDINGS.md` is read
- **THEN** each of H1–H5 is marked held, not held, or not tested with a
  citation to committed numbers or an explicit not-tested reason
