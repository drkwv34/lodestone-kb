# Spec Delta

## MODIFIED Requirements

### Requirement: FR-073 baseline strategies
The system SHALL implement "FR-073" for `classic-rag` (512-token windows,
overlap 64, dense only), `bm25-chunks`, `hybrid-chunks` (BM25 plus dense RRF
k=60), and `lodestone-lexical` (cards plus raw FTS lanes, no embeddings). Each
strategy SHALL expose `index(corpus)` and `retrieve(question, k)` returning
ids. Strategies that are skipped SHALL be reported as skipped with a reason,
never omitted.

#### Scenario: Offline strategies run on synth corpus
- **WHEN** the four in-scope strategies index a `--threads 60` synthetic corpus
  with FakeLLM or hash embedder and retrieve for eval questions
- **THEN** each returns a list of ids and no paid API or network is used

#### Scenario: Skipped strategies are reported
- **WHEN** a run includes a strategy that is skipped (for example
  `full-context` over `context_budget_tokens`)
- **THEN** the report lists it as skipped with a reason and does not drop it
  silently

### Requirement: FR-076 report skeleton
The system SHALL implement "FR-076": `report.md` and `report.json` contain
config hash, corpus hash, versions, per-strategy table, per-category table,
cost/latency table, leakage stats, a caveats section that includes "hash
embedder is not semantic" when the hash embedder was used, and failures.
Body ordering SHALL be stable; timestamps appear only in the header.

#### Scenario: Hash-embedder caveat is present
- **WHEN** a report is generated from an offline hash-embedder run
- **THEN** the caveats section contains the text that the hash embedder is not
  semantic

#### Scenario: Report golden is stable
- **WHEN** a report is built from a fixture result with a fixed header time
- **THEN** markdown body order is stable and no timestamp appears outside the
  header

#### Scenario: Leakage histogram is present
- **WHEN** question generation recorded leakage scores
- **THEN** the report leakage section includes dropped count and a histogram
  rather than an empty placeholder
