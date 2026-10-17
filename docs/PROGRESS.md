# Project progress

| Day | Date (America/Guayaquil) | PR | CI URL | Requirement IDs | Status / deviations |
|---|---|---|---|---|---|---|
| 1 | 2026-10-17 | [#1 — merged](https://github.com/drkwv34/lodestone-kb/pull/1) | [success on dbdea77](https://github.com/drkwv34/lodestone-kb/actions/runs/39058358316) | FR-001, FR-002, FR-082, FR-080 partial; NFR-011, NFR-012 Day 1 gates, NFR-017; FR-005 preview | Merged locally with --no-ff as Christian and pushed main at 443fde2. Real OpenSpec archived as 2026-10-17-day-1-scaffold; strict validation: 2 passed, 0 failed. Archive/evidence committed directly on main at 03432c7 and pushed; annotated day-1 tag published on merge commit 443fde2. Day 1 complete. Local tests: 28 passed, 98.22% coverage. |
| 2 | 2026-10-17 | [#2 — ready, open](https://github.com/drkwv34/lodestone-kb/pull/2) | [success on implementation head cc4d23c](https://github.com/drkwv34/lodestone-kb/actions/runs/39065569808) | FR-010 md/txt/rst, FR-014 hash skeleton, FR-030, FR-032 infrastructure + rare lane, FR-041 source/kind | Implementation complete; 52 tests, 96.15% local coverage. Migration 0002; 0001 unchanged. All nine CI jobs successful on the implementation head; pasted evidence in day-02.md. Final evidence-commit head is verified in PR #2 after push (immutable CI evidence cannot reference its own future run). OpenSpec active. Merge/archive/tag await owner follow-up. |

## Delivery record

- User independently verified green PR-head CI and explicitly authorised completion on 2026-10-17 despite the gh API Forbidden error. CI success is also recorded from the GitHub connector.
- Merge commit: `443fde2271118f00e2111aab3ecaec98ab7eee8e` (Christian author and committer). Published tag `day-1` points to this merge, not the archive or evidence commits.
- The supplied specs remain unchanged. The architecture FTS norm→norm_text correction is documented in decision 0001; the inherited GitHub root committer is preserved. All Day 1 commits after the root use Christian for author and committer, without co-author trailers.
- Day 2 extends the Day 1 foundation with local files ingestion and lexical search only. Full FR-080 diagnostics and future coverage ramps remain scheduled in the original delivery plan.

See [Day 1 evidence](evidence/day-01.md), [Day 2 evidence](evidence/day-02.md) and [Day 1 decisions](decisions/0001-day-1-schema-and-bootstrap.md) and [Day 2 decisions](decisions/0002-day-2-lexical-foundation.md).
