# Spec Delta

## MODIFIED Requirements

### Requirement: FR-050 typed SDK facade
The system SHALL implement "FR-050": `Lodestone.open(path)` with `.sync()`, `.search()`, `.get()`, `.grep()`, `.who_knows()`, `.recent()`, `.stats()`, and a typed `.ask()`; the package is fully typed (`py.typed`) with no global state. `search(explain=True)` SHALL return hits that validate as `evidence.v1` `Evidence` objects, including the nested explain object.

#### Scenario: mypy strict consumer
- **WHEN** a typed consumer imports `Lodestone` and calls the public methods
- **THEN** `mypy --strict` passes on that consumer

#### Scenario: README doctest
- **WHEN** the README SDK snippet is executed as a doctest
- **THEN** it completes without network or paid APIs

#### Scenario: SDK search explain validates
- **WHEN** `Lodestone.search` is called with `explain=True` on a workspace that has fused hits
- **THEN** the call succeeds and each hit validates as `Evidence` with a nested `explain.lanes` object
