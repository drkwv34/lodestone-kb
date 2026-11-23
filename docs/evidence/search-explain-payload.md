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

## PR head CI

- PR: https://github.com/drkwv34/lodestone-kb/pull/18
- Head SHA: `a2fafdba156fe68c2407b4669b9de33dc278b441`
- Run: https://github.com/drkwv34/lodestone-kb/actions/runs/45093707126
- Conclusion: success (10/10 jobs)

## Merge

```text
$ git merge --no-ff fix/search-explain-payload -m "Merge pull request #18 from drkwv34/fix/search-explain-payload"
Merge made by the 'ort' strategy.
```

Merge commit: `e8bbfccf0fb9baa63d28d524fb4423386a7cd981`
Author and committer: Christian Agila `<87576768+drkwv34@users.noreply.github.com>`
Message is exactly one line: `Merge pull request #18 from drkwv34/fix/search-explain-payload`

## Archive (on main)

```text
$ openspec archive fix-search-explain-payload --yes --skip-specs
Task status: ✓ Complete
Skipping spec updates (--skip-specs flag provided).
Change 'fix-search-explain-payload' archived as '2026-11-23-fix-search-explain-payload'.

$ openspec validate --all --strict
✓ spec/beir-adapter
✓ spec/bench-agentic-advise
✓ spec/bench-formats-synth
✓ spec/chunkers-sources
✓ spec/docs-packaging
✓ spec/fusion-search
✓ spec/hardening
✓ spec/lexical-search
✓ spec/mcp-ask
✓ spec/mcp-container
✓ spec/providers-distillation
✓ spec/repository-gates
✓ spec/rerank-sdk-cli
✓ spec/threads-bursts
✓ spec/vector-lanes
✓ spec/workspace-foundation
Totals: 16 passed, 0 failed (16 items)
```

Main specs were synced from the change deltas before `--skip-specs` (FR-037, FR-040,
FR-041, FR-042, FR-050, FR-052). `ruff format .` left 325 files unchanged.
