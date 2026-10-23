# Spec Delta

## Purpose

Keep the foundation portable, typed, tested and license-compatible through
blocking checks that run on every pull request and main-branch update.

## MODIFIED Requirements

### Requirement: NFR-012 initial quality gates
CI SHALL enforce "NFR-012": coverage at least 85% of `src/lodestone`,
mypy --strict, Ruff lint and formatting, import boundaries, and modules no
longer than 500 lines.

#### Scenario: Quality regression
- **WHEN** any blocking gate fails
- **THEN** the PR cannot be considered ready to merge and the check is
  preserved, including the 85% coverage gate
