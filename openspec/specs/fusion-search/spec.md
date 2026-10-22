# fusion-search Specification

## Purpose
Fuse independent retrieval lanes into explainable hybrid search with recency, diversity, neighbour context, a guarded grep lane, versioned evidence packets, and first performance measurements.

## Requirements

### Requirement: FR-034 grep lane
The system SHALL implement "FR-034": lane `grep` performs regex or literal search over raw text of in-scope records, returning line numbers and context lines.

#### Scenario: Regex fixture spans
- **WHEN** a record contains a matching line for a valid regex
- **THEN** the grep lane returns that record with the matching line number and surrounding context

#### Scenario: Catastrophic-regex guard
- **WHEN** a pattern is longer than 500 characters, uses nested quantifiers, or exceeds a 2 s per-query budget
- **THEN** the query is rejected or aborted with a grep timeout or pathological-pattern notice and no unbounded scan proceeds

### Requirement: FR-035 weighted RRF
The system SHALL implement "FR-035": weighted reciprocal rank fusion with default `k=60` over enabled lanes, using configured per-lane weights, with ties broken by `updated_at` descending then id.

#### Scenario: Cerebras figure
- **WHEN** six lists rank a document at 2, 3, 1, 5 and 5 across five lists (absent from the sixth)
- **THEN** the fused RRF score is 0.0792 plus or minus 0.0001

### Requirement: FR-036 recency decay
The system SHALL implement "FR-036": after fusion, multiply each score by `max(floor, 0.5 ** (age_days / half_life_days))` using per-kind config defaults (thread 120 d / 0.4, doc none, code none), disableable per query.

#### Scenario: Newer thread ranks first
- **WHEN** two otherwise-equal threads are 8 months and 2 weeks old
- **THEN** the newer thread ranks first and the older score respects the floor

#### Scenario: Decay disabled
- **WHEN** `--no-decay` or `decay=False` is set
- **THEN** ranking matches the raw fused order without recency

### Requirement: FR-037 dedupe and diversity
The system SHALL implement "FR-037": collapse records that share a `parent_id` into the best-scoring hit, keep `matched_children`, and apply `max_per_source` (default 3) inside the top `candidate_pool` (default 20).

#### Scenario: Six chunks from one file
- **WHEN** six chunks of one file are fused into the pool
- **THEN** the file is listed once with children and at most three hits from that source remain in the pool

### Requirement: FR-038 neighbour expansion
The system SHALL implement "FR-038": for chunk or section hits, attach previous and next siblings (`expand=1` default) with heading text, never exceeding `expand_max_chars` (default 4,000).

#### Scenario: Middle section
- **WHEN** a hit is a middle sibling
- **THEN** the packet includes previous, current and next sections in order

#### Scenario: First last and missing neighbours
- **WHEN** the hit is first, last, or a neighbour row is missing
- **THEN** only existing siblings are attached and expansion still succeeds

### Requirement: FR-040 explainability
The system SHALL implement "FR-040": `--explain` / `explain=True` returns per hit the per-lane rank and score, RRF contribution, decay factor, rerank score and final score.

#### Scenario: Contributions reconstruct the score
- **WHEN** explain is requested on a fused hit
- **THEN** the sum of lane contributions times the decay factor equals the reported final score within 1e-9

### Requirement: FR-042 evidence packet
The system SHALL implement "FR-042": fused search emits versioned `evidence.v1` packets with `id, source, kind, title, uri, snippet, text?, score, lanes, updated_at, author(s), card?, children[], neighbours[]`.

#### Scenario: Schema file validates output
- **WHEN** fused search returns hits
- **THEN** each packet validates against `schemas/evidence.v1.json`

### Requirement: NFR-001 lexical search latency
The system SHALL measure "NFR-001": lexical search (fts_raw+fts_card+fts_rare, fusion, no rerank) p95, targeting <= 50 ms at 20,000 records on a 2024-class laptop and 150 ms on a GitHub-hosted runner.

#### Scenario: Perf test prints p95
- **WHEN** `pytest -m perf` runs the NFR-001 case
- **THEN** the measured p95 milliseconds are printed and the test is excluded from the default pytest run

### Requirement: NFR-002 ingest throughput
The system SHALL measure "NFR-002": heuristic-card ingest throughput excluding embeddings, targeting >= 200 records/s on the same 20,000-record corpus.

#### Scenario: Perf test prints throughput
- **WHEN** `pytest -m perf` runs the NFR-002 case
- **THEN** the measured records per second are printed

### Requirement: NFR-003 incremental sync
The system SHALL measure "NFR-003": incremental no-change sync of 20,000 records completes targeting <= 10 s.

#### Scenario: Perf test prints duration
- **WHEN** `pytest -m perf` runs the NFR-003 case
- **THEN** the measured seconds are printed

### Requirement: Optional rerank before expansion
Fused search SHALL apply FR-039 rerank to the collapsed candidate pool when `rerank=true` (query or config) before neighbour expansion, and SHALL populate `explain.rerank_score` when explain is requested and rerank ran; otherwise `rerank_score` remains null and fused order is unchanged.

#### Scenario: Explain includes rerank score after a successful rerank
- **WHEN** fused search runs with rerank and explain enabled and FakeLLM returns valid scores
- **THEN** each hit's explain object includes a numeric `rerank_score`

#### Scenario: Disabled rerank leaves fused order
- **WHEN** `rerank` is false or omitted
- **THEN** hit order matches fusion without a rerank stage
