# Tasks

## 1. Nested explain packets

- [x] 1.1 Emit `explain_obj.model_dump()` (nested `lanes`) from fused search, validate the full packet, and keep `Explain`/`Evidence` `extra="forbid"`; verify `test_fr_040_explain_contributions_sum_to_fused_score` and `test_fr_042_evidence_packet_schema` pass against nested explain.
- [x] 1.2 Tighten `schemas/evidence.v1.json` explain to nested `lanes` and update CLI human/`--json` plus in-repo tests that summed flattened keys; verify `test_fr_040_fr_034_fused_explain_and_grep_cli` and `test_fr_039_explain_includes_rerank_score`.
- [x] 1.3 Add SDK and MCP tests that `search(explain=True)` validates as `Evidence`; verify `tests/unit/test_explain_payload.py::test_sdk_search_explain_validates` and `tests/integration/test_mcp_stdio.py::test_search_explain_true`.

## 2. Kind-aware collapse and FR-041

- [x] 2.1 When a kind filter is set, collapse uses the best matching member as representative and keeps parent/children context; without a kind filter, collapse to parent stays; verify `tests/unit/test_collapse_kind_filter.py::test_kind_burst_never_returns_thread` and existing `test_fr_037_collapse_and_per_source_cap`.
- [x] 2.2 Post-check every fused hit against `Scope` so kind/source/author/date/metadata filters still hold after collapse; verify `test_fr_041_filters_property_500_combinations` and e2e `search --kind burst --json` on the thread fixture.

## 3. Docs and gates

- [x] 3.1 Record nested-lanes vs flattened dump and kind-filter representatives in `docs/decisions/0009-explain-nested-lanes.md` and align architecture 3.8; verify the ADR number is 0009 and the architecture `explain` line shows `lanes`.
- [x] 3.2 Run `openspec validate fix-search-explain-payload --strict`, ruff, mypy --strict, import-linter, module-size gate, and pytest with coverage >= 85%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
