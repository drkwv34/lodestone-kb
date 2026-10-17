# SPDX-License-Identifier: Apache-2.0
"""Day 1 commands. All operations run locally and require no provider credentials."""

from __future__ import annotations

import json
import platform
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from lodestone.config import Config, ConfigError, load_config, redact
from lodestone.storage.db import SCHEMA_VERSION, StorageError, inspect_database, probe_fts5
from lodestone.workspace import initialise

app = typer.Typer(no_args_is_help=True, help="Lodestone local knowledge workspace.")
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config")
ConfigOption = Annotated[Path, typer.Option("--config", "-c", help="Path to lodestone.toml.")]


def configuration(path: Path) -> Config:
    try:
        return load_config(path)
    except ConfigError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None


@app.command()
def init(path: Annotated[Path, typer.Argument()] = Path(".")) -> None:
    """Create a configuration and schema v1 database, preserving existing data."""
    try:
        already = initialise(path)
    except ConfigError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Initialisation error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(
        "already initialised" if already else "Initialised lodestone.toml and database schema 1"
    )


@config_app.command("show")
def config_show(config: ConfigOption = Path("lodestone.toml")) -> None:
    """Show resolved configuration as JSON with secret fields redacted."""
    typer.echo(json.dumps(redact(configuration(config).model_dump(mode="json")), indent=2))


@app.command()
def doctor(config: ConfigOption = Path("lodestone.toml")) -> None:
    """Probe Python, SQLite, FTS5, and database schema (Day 1 subset of FR-080)."""
    cfg = configuration(config)
    errors: list[str] = []
    typer.echo(f"Python: {platform.python_version()}")
    typer.echo(f"SQLite: {sqlite3.sqlite_version}")
    if sqlite3.sqlite_version_info < (3, 38, 0):
        errors.append("SQLite >= 3.38 required")
    try:
        probe_fts5()
        typer.echo("FTS5: available (identifier tokenizer probe passed)")
    except StorageError as exc:
        errors.append(str(exc))
    try:
        version = inspect_database(cfg.workspace.db_path)
        typer.echo(f"Database schema: {version} (supported: {SCHEMA_VERSION})")
        if version != SCHEMA_VERSION:
            errors.append("Database requires migration; run lodestone init")
    except (sqlite3.Error, StorageError) as exc:
        errors.append(f"Database: {exc}; run lodestone init or upgrade Lodestone")
    for error in errors:
        typer.echo(f"ERROR: {error}", err=True)
    if errors:
        raise typer.Exit(1)
    typer.echo("Doctor: OK (local Day 1 probes)")
