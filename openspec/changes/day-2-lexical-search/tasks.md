## 1. Foundation
- [x] 1.1 Read SRS, architecture, delivery rules, progress and decisions; start at latest main.
- [x] 1.2 Create a real OpenSpec change with quoted requirement IDs.
- [ ] 1.3 Add migration 0002 and transactional FTS/document-frequency maintenance.

## 2. Day 2 implementation
- [ ] 2.1 Implement FR-010 jailed md/txt/rst discovery, gitignore/globs, size/binary skips.
- [ ] 2.2 Implement FR-014 one-file record pipeline and versioned normalised SHA-256 guard.
- [ ] 2.3 Implement FR-030 tokenizer, safe phrase/prefix/OR expressions and BM25 raw lane.
- [ ] 2.4 Implement FR-032 document-frequency/IDF infrastructure and rare lane.
- [ ] 2.5 Implement FR-041 source/kind SQL filters and sync/search CLI.

## 3. Verification and delivery
- [ ] 3.1 Add FR-named tests, fixture corpus, 1,000-string fuzz and resync no-op checks.
- [ ] 3.2 Pass strict OpenSpec, pytest/70% coverage, mypy strict, ruff, imports and module gate.
- [ ] 3.3 Capture E1-E5 and demo in docs/evidence/day-02.md and PR description.
- [ ] 3.4 Push small Christian-authored commits, open ready PR and verify final-head green CI.
