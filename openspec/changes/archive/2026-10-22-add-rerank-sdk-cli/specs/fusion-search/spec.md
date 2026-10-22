# Spec Delta

## ADDED Requirements

### Requirement: Optional rerank before expansion
Fused search SHALL apply FR-039 rerank to the collapsed candidate pool when `rerank=true` (query or config) before neighbour expansion, and SHALL populate `explain.rerank_score` when explain is requested and rerank ran; otherwise `rerank_score` remains null and fused order is unchanged.

#### Scenario: Explain includes rerank score after a successful rerank
- **WHEN** fused search runs with rerank and explain enabled and FakeLLM returns valid scores
- **THEN** each hit's explain object includes a numeric `rerank_score`

#### Scenario: Disabled rerank leaves fused order
- **WHEN** `rerank` is false or omitted
- **THEN** hit order matches fusion without a rerank stage
