# Spec Delta

## MODIFIED Requirements

### Requirement: FR-041 source and kind filters
The system SHALL implement "FR-041": filters by project, source, kind, author, date range (`since`, `until`) and metadata equality, applied before fusion so every hit satisfies them.

#### Scenario: Filtered single-lane output
- **WHEN** a source/kind filter and limit are supplied to search
- **THEN** every returned hit satisfies both filters and identifies its selected lane

#### Scenario: Property test over random combinations
- **WHEN** 500 random filter combinations are applied to a mixed corpus
- **THEN** every returned hit satisfies every supplied filter and there are 0 violations
