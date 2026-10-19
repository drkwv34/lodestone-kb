# Threads connector, whole-thread upsert and bursts

1. Existing schema already allows `thread` and `burst` kinds, `context_prefix`,
   `author` and `authors_json`. No new migration is added; previous migrations
   stay unchanged.
2. Message `ts` values must be ISO-8601 with `Z` or a numeric offset and are
   stored as UTC. Timezone-naive timestamps are rejected and the JSONL line is
   skipped with its line number.
3. A changed thread replaces the parent record, card, burst children and any
   embeddings in one transaction. The parent `id` is kept. Unchanged threads
   skip record writes and only refresh cards from cache.
4. Burst IDF uses `term_stats` after the parent upsert. Default `idf_min=4.0`
   rarely fires on tiny corpora; length and reactions still pass a burst under
   the default threshold of 1.0. Weights and thresholds are Config fields.
5. Thread sources are ingested. Register/list/remove behaviour from source
   management is unchanged.
