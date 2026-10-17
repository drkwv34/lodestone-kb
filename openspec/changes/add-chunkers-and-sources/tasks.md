## 1. Structural chunking
- [ ] 1.1 Implement bounded heading/paragraph/fence chunking and heading-path goldens (FR-015).
- [ ] 1.2 Implement language regex tables, signature outlines and coarse-to-fine code goldens (FR-016, FR-010).

## 2. Incremental records
- [ ] 2.1 Persist parent/child records atomically, including parent_id and sibling seq.
- [ ] 2.2 Count unchanged sync writes and single-file processing; implement tombstone, restore and prune (FR-014).

## 3. Sources, projects and secrets
- [ ] 3.1 Add source add/list/remove/sync with complete cascading cleanup (FR-004).
- [ ] 3.2 Validate projects and apply scope before limits; verify 200 generated queries (FR-003).
- [ ] 3.3 Resolve environment secret overrides without persistence and verify redaction (FR-005).

## 4. Verification
- [ ] 4.1 Run strict OpenSpec validation, coverage, strict typing, lint, import contracts and module limits.
- [ ] 4.2 Paste requirement evidence and demo transcript; publish a ready PR and record successful CI for its head.
