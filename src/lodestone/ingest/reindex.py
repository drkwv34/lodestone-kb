# SPDX-License-Identifier: Apache-2.0
"""Rebuild FTS, cards, or vectors from stored text without contacting sources."""

from __future__ import annotations

import sqlite3

from lodestone.config import Config
from lodestone.distill.apply import CardStats, apply_cards
from lodestone.ingest.embeddings import reindex_vectors
from lodestone.providers import make_chat
from lodestone.providers.offline import offline_scope
from lodestone.storage.db import open_database
from lodestone.vectors.embedder import make_embedder

LANES = {"fts", "vec", "cards"}


def rebuild_fts(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
    connection.execute("INSERT INTO records_card_fts(records_card_fts) VALUES('rebuild')")
    connection.execute("DELETE FROM record_terms")
    connection.execute(
        "INSERT INTO record_terms(record_id, term) "
        "SELECT DISTINCT v.doc, v.term FROM records_vocab v JOIN records r ON r.id=v.doc "
        "WHERE r.tombstoned=0 AND v.col IN ('title', 'text')"
    )


def reindex_cards(connection: sqlite3.Connection, config: Config, *, offline: bool) -> int:
    chat = make_chat(config, None, offline=offline)
    stats = CardStats()
    parents = [
        int(row[0])
        for row in connection.execute(
            "SELECT id FROM records WHERE parent_id IS NULL AND tombstoned=0"
        )
    ]
    with connection:
        for parent_id in parents:
            apply_cards(connection, parent_id, config, chat, stats, refresh=True)
    return stats.cards_llm + stats.cards_heuristic


def reindex_workspace(config: Config, *, lanes: list[str], offline: bool = False) -> dict[str, int]:
    unknown = [lane for lane in lanes if lane not in LANES]
    if unknown:
        raise ValueError(f"unknown reindex lane(s): {', '.join(unknown)}")
    guarded = offline or config.offline
    connection = open_database(config.workspace.db_path)
    payload: dict[str, int] = {}
    try:
        with offline_scope(guarded):
            records = int(
                connection.execute("SELECT count(*) FROM records WHERE tombstoned=0").fetchone()[0]
            )
            payload["records"] = records
            if "fts" in lanes:
                before = int(connection.execute("SELECT count(*) FROM records_fts").fetchone()[0])
                with connection:
                    rebuild_fts(connection)
                after = int(connection.execute("SELECT count(*) FROM records_fts").fetchone()[0])
                payload.update(
                    {"fts_before": before, "fts_after": after, "before": before, "after": after}
                )
            if "cards" in lanes:
                before = int(
                    connection.execute(
                        "SELECT count(*) FROM records WHERE card_json IS NOT NULL AND tombstoned=0"
                    ).fetchone()[0]
                )
                written = reindex_cards(connection, config, offline=guarded)
                after = int(
                    connection.execute(
                        "SELECT count(*) FROM records WHERE card_json IS NOT NULL AND tombstoned=0"
                    ).fetchone()[0]
                )
                payload.update(
                    {
                        "cards_before": before,
                        "cards_after": after,
                        "cards_written": written,
                        "before": before,
                        "after": after,
                    }
                )
            if "vec" in lanes:
                embedder = make_embedder(config, offline=guarded)
                try:
                    if embedder is None:
                        raise ValueError(
                            "embeddings are disabled; set embed.provider or pass --offline"
                        )
                    before = int(
                        connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
                    )
                    with connection:
                        written = reindex_vectors(
                            connection,
                            embedder,
                            config.embed.source,
                            batch_size=config.embed.batch_size,
                        )
                    after = int(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0])
                    payload.update(
                        {
                            "before": before,
                            "after": after,
                            "written": written,
                            "records": records,
                        }
                    )
                finally:
                    closer = getattr(embedder, "close", None)
                    if callable(closer):
                        closer()
            return payload
    finally:
        connection.close()
