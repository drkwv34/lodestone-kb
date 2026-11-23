# Nested search explain packets and kind-filtered collapse

Branch: `fix/search-explain-payload`.
OpenSpec change: `fix-search-explain-payload`.
Base: `b5a57085e92ce83a7f30d1ea1724938f2c64be20`.

Implements nested `explain.lanes` on fused packets (FR-040, FR-042, FR-050,
FR-052) and kind-aware parent collapse so FR-041 still holds after fusion
(FR-037).

## OpenSpec (on the PR head, before archive)

```text
$ openspec --version
2.1.1

$ openspec validate fix-search-explain-payload --strict
Change 'fix-search-explain-payload' is valid
```

## Requirement checklist

- [x] FR-040 nested explain: `test_fr_040_explain_contributions_sum_to_fused_score`, `test_sdk_search_explain_validates`
- [x] FR-042 full packet: `test_fr_042_evidence_packet_schema`, `test_fr_042_validate_packet_rejects_flattened_explain`
- [x] FR-050 SDK: `test_sdk_search_explain_validates`
- [x] FR-052 MCP: `tests/integration/test_mcp_stdio.py::test_search_explain_true`
- [x] FR-037 unfiltered parent collapse: `test_fr_037_collapse_and_per_source_cap`
- [x] FR-041 kind filter after collapse: `test_kind_burst_never_returns_thread`, `test_fr_041_fused_kind_burst_json`

## Tests on base (must fail)

```text
FAILED tests/unit/test_explain_payload.py::test_sdk_search_explain_validates
FAILED tests/integration/test_mcp_stdio.py::test_search_explain_true
FAILED tests/unit/test_collapse_kind_filter.py::test_kind_burst_never_returns_thread
FAILED tests/e2e/test_threads_cli.py::test_fr_041_fused_kind_burst_json
```

SDK/MCP fail with `pydantic_core.ValidationError: Extra inputs are not permitted`
for `explain.fts_raw` / `explain.fts_card` / `explain.vec_card`. Kind-filtered
fused search returns `kind=thread` instead of `burst`.

## Tests after the fix

```text
$ python3 -m pytest -q \
    tests/unit/test_explain_payload.py::test_sdk_search_explain_validates \
    tests/integration/test_mcp_stdio.py::test_search_explain_true \
    tests/unit/test_collapse_kind_filter.py::test_kind_burst_never_returns_thread \
    tests/e2e/test_threads_cli.py::test_fr_041_fused_kind_burst_json \
    --no-cov
....                                                                     [100%]
4 passed
```

Local gates: `ruff check .`, `mypy --strict src`, `lint-imports`,
`scripts/check_modules.py`, `openspec validate fix-search-explain-payload --strict`,
pytest coverage 91% (>= 85%).
