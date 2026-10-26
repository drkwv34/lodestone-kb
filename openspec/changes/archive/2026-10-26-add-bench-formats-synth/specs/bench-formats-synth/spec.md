# Spec Delta

## Purpose

Define the offline RAG-strategy benchmark: evalset and report formats, a
deterministic synthetic corpus, baseline retrieval strategies, parent-collapsed
metrics, a report skeleton, and the fixed-window chunker those baselines use.

## ADDED Requirements

### Requirement: FR-070 evalset.v1 format
The system SHALL implement "FR-070": eval sets are JSONL `evalset.v1` rows with
`qid`, `question`, `gold_ids` (parent `ext_id` values, strategy-independent),
optional `gold_answer_must_contain`, `category`, and optional `source_hint`.
Invalid sets SHALL be rejected with line numbers.

#### Scenario: Valid evalset loads
- **WHEN** a well-formed evalset.v1 JSONL file is loaded
- **THEN** each row exposes qid, question, gold_ids, category, and optional
  fields without error

#### Scenario: Invalid rows report line numbers
- **WHEN** a row is missing required fields, has unknown category, or is not
  JSON
- **THEN** validation fails and the error names the 1-based line number

### Requirement: FR-071 synthetic corpus generator
The system SHALL implement "FR-071": `lodestone bench synth --seed N --threads N`
emits deterministic threads, docs, and code snippets plus an evalset covering
`exact_token`, `paraphrase`, `stale_vs_fresh`, `tangent_in_long_thread`,
`multi_source`, and `unanswerable`. The same seed SHALL produce byte-identical
output.

#### Scenario: Same seed is byte-identical
- **WHEN** synth is run twice with the same seed and thread count
- **THEN** every emitted file is byte-identical and the corpus hash matches the
  pinned test hash

#### Scenario: Categories are present
- **WHEN** synth runs with a positive thread count
- **THEN** the evalset contains at least one question in each of the six
  difficulty categories

### Requirement: FR-073 baseline strategies
The system SHALL implement "FR-073" for `classic-rag` (512-token windows,
overlap 64, dense only), `bm25-chunks`, `hybrid-chunks` (BM25 plus dense RRF
k=60), and `lodestone-lexical` (cards plus raw FTS lanes, no embeddings). Each
strategy SHALL expose `index(corpus)` and `retrieve(question, k)` returning
ids. Unimplemented strategies SHALL be reported as skipped, never omitted.

#### Scenario: Offline strategies run on synth corpus
- **WHEN** the four in-scope strategies index a `--threads 60` synthetic corpus
  with FakeLLM or hash embedder and retrieve for eval questions
- **THEN** each returns a list of ids and no paid API or network is used

#### Scenario: Skipped strategies are reported
- **WHEN** a run requests strategies that are not implemented in this change
- **THEN** the report lists them as skipped with a reason and does not drop
  them silently

### Requirement: FR-074 retrieval cost latency metrics
The system SHALL implement "FR-074" retrieval metrics: recall@{1,5,10,20}, MRR,
and nDCG@10 against gold ids after parent-collapse so chunk and card strategies
are comparable; plus tokens in/out and USD from the price table; latency
p50/p95/p99 per query; and index build time and bytes.

#### Scenario: Metric goldens match hand computation
- **WHEN** recall, MRR, and nDCG@10 are computed on a tiny ranked list with
  known gold ids
- **THEN** the values match the independently hand-computed figures

#### Scenario: Parent collapse compares chunk and card hits
- **WHEN** a chunk strategy returns window ids and a card strategy returns
  parent ids for the same gold parent
- **THEN** both map to the parent `ext_id` before metrics are computed

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

### Requirement: Window chunker for bench baselines
The system SHALL provide a fixed-window chunker of 512 tokens with overlap 64
used by classic-rag, bm25-chunks, and hybrid-chunks. Windows SHALL be
deterministic for the same input text.

#### Scenario: Overlapping windows
- **WHEN** a document longer than 512 tokens is windowed
- **THEN** consecutive windows overlap by 64 tokens and remain ordered
