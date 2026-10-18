# repository-gates Specification

## Purpose
Keep the foundation portable, typed, tested and license-compatible through
blocking checks that run on every pull request and main-branch update.

## Requirements

### Requirement: NFR-011 portability
CI SHALL enforce "NFR-011" with Ubuntu Python 3.11, 3.12, 3.13, macOS Python 3.12,
and Windows Python 3.12 smoke tests.

#### Scenario: Portable workspace smoke test
- **WHEN** each matrix job executes
- **THEN** init, doctor, config display and packaged migration resources work

### Requirement: NFR-012 initial quality gates
CI SHALL enforce "NFR-012" at its initial ramp: coverage at least 70%, mypy --strict,
Ruff lint and formatting, import boundaries, and modules no longer than 500 lines.

#### Scenario: Quality regression
- **WHEN** any blocking gate fails
- **THEN** the PR cannot be considered ready to merge and the check is preserved

### Requirement: NFR-017 licensing
The repository SHALL implement "NFR-017": full Apache-2.0 LICENSE, NOTICE, SPDX
source headers and a generated dependency license report rejecting GPL/AGPL.

#### Scenario: Dependency license gate
- **WHEN** CI audits the installed dependencies
- **THEN** it publishes a license report and fails on GPL or AGPL licenses
