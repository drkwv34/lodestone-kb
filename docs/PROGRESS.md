# Project progress

| Day | Date (America/Guayaquil) | PR | CI URL | Requirement IDs | Status / deviations |
|---|---|---|---|---|---|---|
| 1 | 2026-10-17 | [#1 — merged](https://github.com/drkwv34/lodestone-kb/pull/1) | [success on dbdea77](https://github.com/drkwv34/lodestone-kb/actions/runs/39058358316) | FR-001, FR-002, FR-082, FR-080 partial; NFR-011, NFR-012 Day 1 gates, NFR-017; FR-005 preview | Merged locally with --no-ff as Christian and pushed main at 443fde2. Real OpenSpec archived as 2026-10-17-day-1-scaffold; strict validation: 2 passed, 0 failed. Archive/evidence committed directly on main at 03432c7 and pushed; annotated day-1 tag published on merge commit 443fde2. Day 1 complete. Local tests: 28 passed, 98.22% coverage. |
| 2 | 2026-10-17 | [#2 — merged](https://github.com/drkwv34/lodestone-kb/pull/2) | [success on final PR head 927fb4a](https://github.com/drkwv34/lodestone-kb/actions/runs/39065777458) | FR-010 md/txt/rst, FR-014 hash skeleton, FR-030, FR-032 infrastructure + rare lane, FR-041 source/kind | Merged with --no-ff and pushed main at c8f34ae. Archived as 2026-10-17-day-2-lexical-search directly on main; strict OpenSpec validation: 3 passed, 0 failed. Final PR-head E1–E5 and post-merge outputs in day-02.md. All nine PR CI jobs green; 52 tests, 96.15% coverage. Annotated day-2 tag published on merge commit c8f34ae, not the later archive/evidence commits. Day 2 complete. |

## Delivery record

- User independently verified green PR-head CI and explicitly authorised completion on 2026-10-17 despite the gh API Forbidden error. CI success is also recorded from the GitHub connector.
- Merge commit: `443fde2271118f00e2111aab3ecaec98ab7eee8e` (Christian author and committer). Published tag `day-1` points to this merge, not the archive or evidence commits.
- The supplied specs remain unchanged. The architecture FTS norm→norm_text correction is documented in decision 0001; the inherited GitHub root committer is preserved. All Day 1 commits after the root use Christian for author and committer, without co-author trailers.
- Day 2 extends the Day 1 foundation with local files ingestion and lexical search only. Full FR-080 diagnostics and future coverage ramps remain scheduled in the original delivery plan.

See [Day 1 evidence](evidence/day-01.md), [Day 2 evidence](evidence/day-02.md) and [Day 1 decisions](decisions/0001-day-1-schema-and-bootstrap.md) and [Day 2 decisions](decisions/0002-day-2-lexical-foundation.md).

## Day 2 completion record

- Owner independently verified the approved PR head and clean authorship, then authorised merge, direct-on-main archive, and tag.
- Merge commit: `c8f34aedea0b12a38b378e83fa3457db97037a30`; author and committer are Christian Agila <87576768+drkwv34@users.noreply.github.com>.
- OpenSpec archive: `2026-10-17-day-2-lexical-search`; no active changes remain. The archive-generated Purpose placeholder was completed before strict validation passed; no requirement or gate was weakened.
- Archive/evidence commit `38c7d92` was pushed directly on main. Annotated `day-2` was then pushed and resolves to `c8f34aedea0b12a38b378e83fa3457db97037a30`, the merge commit. No Day 3 implementation has started.
