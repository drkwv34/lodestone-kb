-- SPDX-License-Identifier: Apache-2.0
-- Keep external-content FTS and active raw/title document frequencies transactional.
CREATE VIRTUAL TABLE records_vocab USING fts5vocab(records_fts, instance);
CREATE TABLE record_terms(
  record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
  term TEXT NOT NULL,
  PRIMARY KEY(record_id, term)
);
CREATE INDEX record_terms_term ON record_terms(term);
INSERT INTO meta(key, value) VALUES ('record_count',
  (SELECT CAST(count(*) AS TEXT) FROM records WHERE tombstoned=0));
DELETE FROM term_stats;
INSERT INTO records_fts(records_fts) VALUES ('rebuild');
INSERT INTO record_terms(record_id, term)
  SELECT DISTINCT v.doc, v.term FROM records_vocab v JOIN records r ON r.id=v.doc
  WHERE r.tombstoned=0 AND v.col IN ('title', 'text');
INSERT INTO term_stats(term, df) SELECT term, count(*) FROM record_terms GROUP BY term;

CREATE TRIGGER record_terms_ai AFTER INSERT ON record_terms BEGIN
  INSERT INTO term_stats(term, df) VALUES (new.term, 1)
    ON CONFLICT(term) DO UPDATE SET df=df+1;
END;
CREATE TRIGGER record_terms_ad AFTER DELETE ON record_terms BEGIN
  UPDATE term_stats SET df=df-1 WHERE term=old.term;
  DELETE FROM term_stats WHERE term=old.term AND df=0;
END;
CREATE TRIGGER records_ai AFTER INSERT ON records BEGIN
  INSERT INTO records_fts(rowid, title, text, norm_text)
    VALUES (new.id, new.title, new.text, new.norm_text);
  INSERT INTO record_terms(record_id, term)
    SELECT DISTINCT new.id, term FROM records_vocab
    WHERE doc=new.id AND col IN ('title', 'text') AND new.tombstoned=0;
  UPDATE meta SET value=CAST(value AS INTEGER)+(new.tombstoned=0) WHERE key='record_count';
END;
CREATE TRIGGER records_ad AFTER DELETE ON records BEGIN
  DELETE FROM record_terms WHERE record_id=old.id;
  INSERT INTO records_fts(records_fts, rowid, title, text, norm_text)
    VALUES ('delete', old.id, old.title, old.text, old.norm_text);
  UPDATE meta SET value=CAST(value AS INTEGER)-(old.tombstoned=0) WHERE key='record_count';
END;
CREATE TRIGGER records_au AFTER UPDATE ON records BEGIN
  DELETE FROM record_terms WHERE record_id=old.id;
  INSERT INTO records_fts(records_fts, rowid, title, text, norm_text)
    VALUES ('delete', old.id, old.title, old.text, old.norm_text);
  INSERT INTO records_fts(rowid, title, text, norm_text)
    VALUES (new.id, new.title, new.text, new.norm_text);
  INSERT INTO record_terms(record_id, term)
    SELECT DISTINCT new.id, term FROM records_vocab
    WHERE doc=new.id AND col IN ('title', 'text') AND new.tombstoned=0;
  UPDATE meta SET value=CAST(value AS INTEGER)+(new.tombstoned=0)-(old.tombstoned=0)
    WHERE key='record_count';
END;
