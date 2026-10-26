# bench-agentic-advise Specification

## Purpose
Complete the offline RAG-strategy benchmark: remaining strategies, leakage-filtered
question generation, correctness and optional judge, bootstrap statistics, advise
rules R1–R4, and a resume cache that avoids duplicate LLM calls.

## Requirements

### Requirement: FR-072 question generation and leakage
The system SHALL sample records stratified by source and kind, ask the chat
provider for 1–3 user questions per record without quoting the gold text, score
leakage as Jaccard overlap of question tokens with gold-record tokens, drop
questions above `leakage_max` (default 0.5), store category tags, and include a
leakage histogram on the report.

#### Scenario: Leakage filter drops expected questions
- **WHEN** FakeLLM returns one low-overlap question and one question that quotes
  gold-record tokens above `leakage_max`
- **THEN** leakage is computed for both, the high-leakage question is dropped,
  and the report histogram counts the dropped question

### Requirement: FR-073 remaining strategies
The system SHALL implement `lodestone-hybrid` (lexical plus vec lanes),
`lodestone-rerank` (hybrid plus LLM rerank), `agentic-ask` (ask pipeline;
retrieval is the union of cited evidence), `grep-agent` (LLM loop with grep and
read tools only, max 8 tool calls), and `full-context` (whole corpus in the
prompt when at or under `context_budget_tokens`).

#### Scenario: Offline remaining strategies run
- **WHEN** the five remaining strategies index a synthetic corpus with FakeLLM
  and the hash embedder
- **THEN** each returns ids or is reported skipped with a reason, and no paid
  API or network is used

#### Scenario: Full-context over budget is skipped
- **WHEN** `full-context` indexes a corpus whose token count exceeds
  `context_budget_tokens`
- **THEN** the strategy is reported as skipped with reason `too_large` and is
  not omitted from the report

### Requirement: FR-074 correctness and optional judge
The system SHALL score answer correctness by `gold_answer_must_contain`
substring match, and SHALL optionally apply an LLM judge when `--judge` is set.
Failures SHALL count as misses and SHALL never be dropped.

#### Scenario: Must-contain correctness
- **WHEN** an answer contains every `gold_answer_must_contain` needle
- **THEN** correctness is 1.0

#### Scenario: Optional judge uses FakeLLM
- **WHEN** `--judge` is set and FakeLLM returns a numeric score in [0, 1]
- **THEN** that score is recorded as judge correctness without a network call

### Requirement: FR-075 bootstrap statistics
The system SHALL compute 95% percentile bootstrap CIs (default 2,000 resamples,
seeded) per metric, paired bootstrap differences versus a baseline (default
`classic-rag`) with `significant` true when the CI excludes 0, and
per-category breakdowns.

#### Scenario: Seeded bootstrap on a known distribution
- **WHEN** bootstrap CIs are computed on a fixed vector with a fixed seed and
  2,000 resamples
- **THEN** the interval is reproducible on a second run with the same seed

#### Scenario: Paired significance flag
- **WHEN** paired differences versus the baseline have a CI that excludes 0
- **THEN** `significant` is true; when the CI includes 0, `significant` is false

### Requirement: FR-077 advise rules
`lodestone bench advise` SHALL emit one deterministic verdict from rules R1–R4
in that order, each with evidence lines that reference report cells: embeddings
do not pay (R1), context stuffing + caching (R2), distillation helps (R3), or
hybrid default (R4).

#### Scenario: R1 embeddings do not pay
- **WHEN** advise is given a crafted report where lexical recall@10 is within
  3 pp of the best embedding strategy and the paired CI includes 0
- **THEN** the verdict is "embeddings do not pay for themselves on this corpus"
  and evidence lines name the compared cells

#### Scenario: R2 context stuffing
- **WHEN** advise is given a crafted report where `full-context` is feasible,
  its correctness CI is at least the best retrieval strategy, and cost/query
  is at most 3x
- **THEN** the verdict is "consider context stuffing + caching"

#### Scenario: R3 distillation helps
- **WHEN** advise is given a crafted report where a cards strategy beats
  `classic-rag` significantly on `paraphrase` or `tangent_in_long_thread`
- **THEN** the verdict is "distillation helps"

#### Scenario: R4 hybrid default
- **WHEN** advise is given a crafted report that matches none of R1–R3
- **THEN** the verdict is "hybrid default" with evidence lines

### Requirement: FR-078 resume cache
The system SHALL cache per-question results keyed by strategy, config hash,
corpus hash, and qid so an interrupted run resumes without re-spending tokens.

#### Scenario: Resume performs zero duplicate LLM calls
- **WHEN** a run is interrupted after caching some qids and is resumed with
  the same strategy, config hash, and corpus hash
- **THEN** cached qids perform 0 additional LLM calls
