# Spec Delta

## MODIFIED Requirements

### Requirement: FR-037 dedupe and diversity
The system SHALL implement "FR-037": collapse records that share a `parent_id` into the best-scoring hit, keep `matched_children`, and apply `max_per_source` (default 3) inside the top `candidate_pool` (default 20). When a kind filter is supplied, the representative SHALL be the best member that satisfies the filter; the parent stays in parent/children context. Without a kind filter, the representative SHALL remain the parent.

#### Scenario: Six chunks from one file
- **WHEN** six chunks of one file are fused into the pool
- **THEN** the file is listed once with children and at most three hits from that source remain in the pool

#### Scenario: Kind-filtered burst stays a burst
- **WHEN** fused search runs with a kind filter of `burst` on a thread that has a matching burst child
- **THEN** every returned hit has kind `burst` and none has kind `thread`

#### Scenario: Unfiltered collapse still lists the parent
- **WHEN** fused search runs with no kind filter on the same parent/child group
- **THEN** the listed hit is the parent and matching children remain in the packet children list

### Requirement: FR-040 explainability
The system SHALL implement "FR-040": `--explain` / `explain=True` returns per hit the per-lane rank and score, RRF contribution, decay factor, rerank score and final score. The explain object SHALL use a nested `lanes` map (not flattened lane names as extra keys) and SHALL validate against the `Explain` model with extra fields forbidden.

#### Scenario: Contributions reconstruct the score
- **WHEN** explain is requested on a fused hit
- **THEN** the sum of lane contributions times the decay factor equals the reported final score within 1e-9

#### Scenario: Nested lanes object
- **WHEN** fused search returns a hit with explain enabled
- **THEN** `explain.lanes` is an object keyed by lane name, each value has `rank` and contribution fields, and top-level explain keys are only `lanes`, `rrf`, `decay_factor`, `rerank_score`, and `final`

### Requirement: FR-042 evidence packet
The system SHALL implement "FR-042": fused search emits versioned `evidence.v1` packets with `id, source, kind, title, uri, snippet, text?, score, lanes, updated_at, author(s), card?, children[], neighbours[]`. When explain is present the packet SHALL include the nested explain object and the full packet SHALL validate against `schemas/evidence.v1.json`.

#### Scenario: Schema file validates output
- **WHEN** fused search returns hits
- **THEN** each packet validates against `schemas/evidence.v1.json`

#### Scenario: Full packet including explain
- **WHEN** fused search returns hits with explain enabled
- **THEN** each packet including `explain` validates against `schemas/evidence.v1.json` and against the `Evidence` model with extra fields forbidden
