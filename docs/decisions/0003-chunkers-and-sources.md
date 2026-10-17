# Structural chunking and source boundaries

1. Existing schema fields already support file parents, ordered children, project
   membership and tombstones. No migration is required; previous migrations and
   supplied specifications remain unchanged.
2. Parent records retain the complete original file text and stable `(source_id,
   ext_id)` identity. Code parents carry the signature outline in `context_prefix`.
   Section/code children retain exact character spans in metadata, zero-based
   sibling `seq`, and a direct file `parent_id`. Changed parents clear stale cards
   and embeddings and replace their children within the same transaction. Child
   identifiers use the relative path plus `#section:N` or `#code:N`.
3. Hashes include normalized source text, language, both chunker versions and chunk
   settings. Changing chunk settings intentionally reprocesses affected files.
   A hash match skips chunking and record writes; upstream metadata-only changes
   do not reprocess content. Normalization follows the existing NFC/newline rule.
4. Markdown supports ATX/setext headings and backtick/tilde fences. Paragraphs pack
   towards the configured target; oversized units split at newline/space then
   character boundaries. Code matches masked text using language regex tables,
   always isolates methods, and refines oversized methods at control blocks. It
   is a coarse parser; unsupported syntax falls back to lossless bounded chunks.
5. Deleted files tombstone the parent and children. Search and term frequencies
   exclude them immediately; `--prune` physically removes their dependent data.
   External-content FTS retains tombstone text until purge to preserve its backing
   table integrity. Skipped paths retain their previous indexed contents; a failed
   directory scan cannot trigger missing-file cleanup. Source removal cascades
   through records, FTS triggers, terms, embeddings and project membership.
6. TOML defines the complete source/project registry. Explicit project membership
   is authoritative; empty means no sources. Only configurations omitting projects
   infer an all-source `default`. The configured default and named `default` must
   exist; names and source references are validated. Query source filters intersect
   project membership before SQL ordering/limits. Removing TOML sources reconciles
   the database on the next successful sync.
7. Source mutations re-emit TOML values without retaining comments/formatting and
   atomically replace the configuration through a private temporary sibling file.
   SQLite mutations roll back if replacement fails. Configuration and SQLite do
   not share a crash-atomic commit; TOML remains authoritative for reconciliation.
   File sources can be synced; thread sources can be registered/listed/removed,
   while thread ingestion remains outside this feature.
8. Endpoint secret resolution checks `LODESTONE_LLM_API_KEY` or
   `LODESTONE_EMBED_API_KEY`, then the configured `api_key_env`. Secrets are returned
   as `SecretStr`, never assigned to configuration or persisted. No provider calls
   are introduced.
