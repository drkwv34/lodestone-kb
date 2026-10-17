# Day 2 lexical foundation

The Day 2 scope is exactly FR-010 (md/txt/rst), FR-014 (hash skeleton), FR-030,
FR-032 (infrastructure plus the requested rare lane), and FR-041 (source/kind).
The supplied specifications and migration 0001 remain unchanged.

1. Migration 0002 rebuilds the existing external-content FTS index, then installs
   insert/update/delete triggers. `record_terms` stores distinct raw/title tokens
   per active record; its triggers maintain `term_stats`. `meta.record_count`
   caches active N. FTS retains all backing rows, including tombstones, so FTS's
   external-content integrity check remains valid; queries exclude tombstones.
   Raw/title df excludes `norm_text`. Upserts, source cascades, tombstone state
   changes and rollbacks keep all these structures consistent in one transaction.
2. `tokenize.py` uses a temporary SQLite unicode61 index with the exact persistent
   tokenizer options. SQLite, rather than a Python approximation with a different
   Unicode version, owns case folding/diacritics. Tokens retain `_` and `-`.
   Queries quote all terms, preserve phrases and trailing prefix stars, OR-expand
   ordinary words, and cap input/clauses at 16,384 characters/64 clauses. Operators
   supplied by users are literal terms. Lone Unicode surrogates become replacement
   characters rather than encoding failures. No persistent tokenizer state exists.
3. IDF is the architecture's natural-log BM25 formula. At N=10,000, IDF >=4
   corresponds to roughly df/N <=1.83%; on a tiny corpus no term may qualify.
   `rare_df_ratio`, when set, overrides the absolute IDF threshold. The rare lane
   ORs only qualifying, known query tokens and returns no hits if none qualify.
4. The files connector reads UTF-8 md/txt/rst with a configurable per-source
   `max_file_bytes` (default 1 MiB); it checks the whole bounded payload for binary
   controls/invalid UTF-8. Root and nested gitignore rules use existing pathspec.
   Gitignore reads have their own 1 MiB cap, independent of document limits; an
   unreadable/invalid/oversize gitignore skips its subtree rather than losing its
   rules. File symlinks are accepted only inside the resolved source root.
   Directory symlinks are skipped to prevent cycles. Include/exclude patterns
   cannot contain absolute paths or `..` traversal.
5. File v0 records are `kind=doc`, keyed by source plus relative POSIX path.
   SHA-256 covers `file-v0`, a NUL separator, and NFC text with CRLF/CR normalised
   to LF. Raw UTF-8 text is preserved. Unchanged normalised content does not write
   records, FTS, stats, or registry metadata; `last_synced_at` advances when content
   is processed. Cards/embeddings remain pending for their delivery days. Upstream
   deletion, pruning and structural chunks stay on Day 3.
6. `sync` and `search` extend the Day 1 CLI and workspace lifecycle. Search opens
   read-only and asks for migration via init when necessary. Output is a selected
   single lane, with positive `-bm25` scores, source/kind SQL filters, deterministic
   score/updated_at/id ordering and optional JSON. Project scoping, complete SDK,
   fusion and evidence.v1 remain on their scheduled days. The existing import
   contract stays intact and a second contract covers the new layers.
7. The user explicitly requires stopping before merge. The OpenSpec change remains
   active. Merge, archive as a direct commit on main, and day-2 tagging await the
   follow-up. Evidence commits necessarily follow the CI run whose output they
   embed; the final PR description records the subsequent final-head CI output,
   while the committed evidence retains the clearly identified implementation
   checkpoint. The post-merge archive/evidence commit can copy that final-head
   output without changing the tested PR head.
