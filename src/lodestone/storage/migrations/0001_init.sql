-- SPDX-License-Identifier: Apache-2.0
-- Connection PRAGMAs and transactional user_version stamping are managed by db.py.
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, config_json TEXT NOT NULL,
  last_synced_at TEXT);
CREATE TABLE projects(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT);
CREATE TABLE project_sources(project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
  source_id INTEGER REFERENCES sources(id) ON DELETE CASCADE, PRIMARY KEY(project_id, source_id));
CREATE TABLE records(
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  ext_id TEXT NOT NULL,                 -- stable id inside source (path#section, thread_id, thread_id#burst3)
  parent_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('doc','section','code_file','code','thread','burst')),
  seq INTEGER NOT NULL DEFAULT 0,       -- order among siblings (neighbour expansion)
  title TEXT NOT NULL DEFAULT '',
  text TEXT NOT NULL,                   -- raw text, verbatim
  context_prefix TEXT NOT NULL DEFAULT '',
  card_json TEXT,                       -- distilled card or NULL
  card_method TEXT,                     -- 'llm' | 'heuristic' | NULL
  norm_text TEXT NOT NULL DEFAULT '',   -- text indexed for fts_card / embedded
  author TEXT, authors_json TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT NOT NULL,
  derived_state TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,    -- UTC ISO-8601 of the upstream item
  indexed_at TEXT NOT NULL,
  tombstoned INTEGER NOT NULL DEFAULT 0,
  UNIQUE(source_id, ext_id)
);
CREATE INDEX records_parent ON records(parent_id, seq);
CREATE INDEX records_updated ON records(updated_at);
CREATE INDEX records_kind ON records(kind, source_id);
CREATE VIRTUAL TABLE records_fts USING fts5(title, text, norm_text, content='records', content_rowid='id',
  tokenize="unicode61 remove_diacritics 2 tokenchars '_-'");
-- triggers keep records_fts in sync (external-content table): AFTER INSERT/UPDATE/DELETE on records
CREATE TABLE term_stats(term TEXT PRIMARY KEY, df INTEGER NOT NULL);   -- df over non-tombstoned records of kinds doc/section/thread/code/code_file/burst
CREATE TABLE card_cache(key TEXT PRIMARY KEY, card_json TEXT NOT NULL, method TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE embeddings(record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('card','chunk','burst')), model TEXT NOT NULL, dim INTEGER NOT NULL,
  vec BLOB NOT NULL, PRIMARY KEY(record_id, kind, model));
CREATE TABLE llm_log(id INTEGER PRIMARY KEY, op TEXT, model TEXT, in_tokens INTEGER, out_tokens INTEGER,
  latency_ms INTEGER, ok INTEGER, created_at TEXT);
CREATE TABLE query_log(id INTEGER PRIMARY KEY, qhash TEXT, project TEXT, lanes TEXT, results INTEGER,
  latency_ms INTEGER, query_text TEXT, created_at TEXT);
