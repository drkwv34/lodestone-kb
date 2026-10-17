# SPDX-License-Identifier: Apache-2.0
"""Idempotent source and project registry reconciliation."""

import sqlite3

from lodestone.config import Config, Source


def register(connection: sqlite3.Connection, source: Source) -> int:
    connection.execute(
        "INSERT INTO sources(name,kind,config_json) VALUES(?,?,?) "
        "ON CONFLICT(name) DO UPDATE SET kind=excluded.kind,config_json=excluded.config_json "
        "WHERE kind<>excluded.kind OR config_json<>excluded.config_json",
        (source.name, source.kind, source.model_dump_json()),
    )
    row = connection.execute("SELECT id FROM sources WHERE name=?", (source.name,)).fetchone()
    return int(row[0])


def reconcile(connection: sqlite3.Connection, config: Config) -> None:
    """Reflect explicit membership while leaving retained records intact."""
    config.validate_registry()
    wanted_sources = {source.name for source in config.sources}
    for (name,) in connection.execute("SELECT name FROM sources").fetchall():
        if name not in wanted_sources:
            connection.execute("DELETE FROM sources WHERE name=?", (name,))
    for source in config.sources:
        register(connection, source)
    wanted = {project.name for project in config.projects}
    for (name,) in connection.execute("SELECT name FROM projects").fetchall():
        if name not in wanted:
            connection.execute("DELETE FROM projects WHERE name=?", (name,))
    for project in config.projects:
        connection.execute("INSERT OR IGNORE INTO projects(name) VALUES(?)", (project.name,))
        project_id = connection.execute(
            "SELECT id FROM projects WHERE name=?", (project.name,)
        ).fetchone()[0]
        current = dict(
            connection.execute(
                "SELECT s.name,s.id FROM sources s JOIN project_sources p ON p.source_id=s.id "
                "WHERE p.project_id=?",
                (project_id,),
            )
        )
        for name, source_id in current.items():
            if name not in project.sources:
                connection.execute(
                    "DELETE FROM project_sources WHERE project_id=? AND source_id=?",
                    (project_id, source_id),
                )
        for name in project.sources:
            if name not in current:
                connection.execute(
                    "INSERT INTO project_sources(project_id,source_id) "
                    "SELECT ?,id FROM sources WHERE name=?",
                    (project_id, name),
                )
