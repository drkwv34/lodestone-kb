## Why
Day 1 creates an offline workspace but cannot ingest or retrieve documents. Day 2
adds a local lexical path over text corpora while preserving the existing foundation.

## What Changes
- Implement "FR-010" for md/txt/rst: jailed, bounded discovery with globs and gitignore.
- Implement "FR-014" hash skeleton: one record per file and unchanged-record no-op.
- Implement "FR-030": safe FTS5 expressions and title/text BM25 retrieval.
- Implement "FR-032" infrastructure: transactional document frequencies, IDF, rare lane.
- Implement "FR-041" source/kind filters before lane ranking.
- Add forward migration 0002, fixtures, CLI sync/search, and delivery evidence.

## Capabilities
### New Capabilities
- `lexical-search`: local file ingestion and single-lane lexical retrieval.

## Impact
Existing schema upgrades forward without editing 0001. No paid APIs or new runtime
dependencies. Chunking, complete incremental deletion/pruning, projects, cards,
fusion, SDK and further filters retain their scheduled later-day scope. The change
stays active until the owner authorises merge; archive/tag follow in a later run.
