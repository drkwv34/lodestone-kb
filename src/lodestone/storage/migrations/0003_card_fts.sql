-- SPDX-License-Identifier: Apache-2.0
-- Recreate raw FTS over title/text only; index cards in a dedicated table.
DROP TRIGGER IF EXISTS records_ai;
DROP TRIGGER IF EXISTS records_ad;
DROP TRIGGER IF EXISTS records_au;
DROP TABLE IF EXISTS records_vocab;
DROP TABLE IF EXISTS records_fts;

CREATE VIRTUAL TABLE records_fts USING fts5(
  title, text, content='records', content_rowid='id',
  tokenize="unicode61 remove_diacritics 2 tokenchars '_-'"
);
CREATE VIRTUAL TABLE records_vocab USING fts5vocab(records_fts, instance);
CREATE VIRTUAL TABLE records_card_fts USING fts5(
  norm_text, content='records', content_rowid='id',
  tokenize="unicode61 remove_diacritics 2 tokenchars '_-'"
);

INSERT INTO records_fts(rowid, title, text) SELECT id, title, text FROM records;
INSERT INTO records_card_fts(rowid, norm_text) SELECT id, norm_text FROM records;

CREATE TRIGGER records_ai AFTER INSERT ON records BEGIN
  INSERT INTO records_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
  INSERT INTO records_card_fts(rowid, norm_text) VALUES (new.id, new.norm_text);
  INSERT INTO record_terms(record_id, term)
    SELECT DISTINCT new.id, term FROM records_vocab
    WHERE doc=new.id AND col IN ('title', 'text') AND new.tombstoned=0;
  UPDATE meta SET value=CAST(value AS INTEGER)+(new.tombstoned=0) WHERE key='record_count';
END;
CREATE TRIGGER records_ad AFTER DELETE ON records BEGIN
  DELETE FROM record_terms WHERE record_id=old.id;
  INSERT INTO records_fts(records_fts, rowid, title, text)
    VALUES ('delete', old.id, old.title, old.text);
  INSERT INTO records_card_fts(records_card_fts, rowid, norm_text)
    VALUES ('delete', old.id, old.norm_text);
  UPDATE meta SET value=CAST(value AS INTEGER)-(old.tombstoned=0) WHERE key='record_count';
END;
CREATE TRIGGER records_au AFTER UPDATE ON records BEGIN
  DELETE FROM record_terms WHERE record_id=old.id;
  INSERT INTO records_fts(records_fts, rowid, title, text)
    VALUES ('delete', old.id, old.title, old.text);
  INSERT INTO records_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
  INSERT INTO records_card_fts(records_card_fts, rowid, norm_text)
    VALUES ('delete', old.id, old.norm_text);
  INSERT INTO records_card_fts(rowid, norm_text) VALUES (new.id, new.norm_text);
  INSERT INTO record_terms(record_id, term)
    SELECT DISTINCT new.id, term FROM records_vocab
    WHERE doc=new.id AND col IN ('title', 'text') AND new.tombstoned=0;
  UPDATE meta SET value=CAST(value AS INTEGER)+(new.tombstoned=0)-(old.tombstoned=0)
    WHERE key='record_count';
END;
