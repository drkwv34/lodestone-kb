# SPDX-License-Identifier: Apache-2.0
"""Local workspace and lexical commands; no provider credentials required."""

from __future__ import annotations

import json
import os
import platform
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal

import typer

from lodestone.config import Config, ConfigError, Source, load_config, redact
from lodestone.lanes.fts import LaneName
from lodestone.providers import ProviderError
from lodestone.storage.db import SCHEMA_VERSION, StorageError, inspect_database, probe_fts5
from lodestone.workspace import (
    cost_workspace,
    get_workspace,
    initialise,
    search_workspace,
    source_list,
    sync_workspace,
    update_source,
)

app = typer.Typer(no_args_is_help=True, help="Lodestone local knowledge workspace.")
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config")
source_app = typer.Typer(no_args_is_help=True)
app.add_typer(source_app, name="source")
ConfigOption = Annotated[Path, typer.Option("--config", "-c", help="Path to lodestone.toml.")]


def configuration(path: Path) -> Config:
    try:
        return load_config(path)
    except ConfigError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None


@app.command()
def init(path: Annotated[Path, typer.Argument()] = Path(".")) -> None:
    """Create a configuration and current-schema database, preserving existing data."""
    try:
        already = initialise(path)
    except ConfigError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Initialisation error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(
        "already initialised"
        if already
        else f"Initialised lodestone.toml and database schema {SCHEMA_VERSION}"
    )


@config_app.command("show")
def config_show(config: ConfigOption = Path("lodestone.toml")) -> None:
    """Show resolved configuration as JSON with secret fields redacted."""
    typer.echo(json.dumps(redact(configuration(config).model_dump(mode="json")), indent=2))


@app.command()
def doctor(config: ConfigOption = Path("lodestone.toml")) -> None:
    """Probe Python, SQLite, FTS5, and database schema (subset of FR-080)."""
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
    typer.echo("Doctor: OK (local schema probes)")


@app.command()
def sync(
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
    source: Annotated[list[str] | None, typer.Option()] = None,
    prune: Annotated[bool, typer.Option()] = False,
    provider: Annotated[str | None, typer.Option(help="fake or config.")] = None,
    refresh_cards: Annotated[bool, typer.Option("--refresh-cards")] = False,
) -> None:
    """Sync files and thread JSONL sources; optionally purge missing items."""
    cfg = configuration(config)
    try:
        report = sync_workspace(
            cfg,
            sources=source,
            project=project,
            prune=prune,
            provider=provider,
            refresh_cards=refresh_cards,
        )
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except ProviderError as exc:
        typer.echo(f"Provider error: {exc}", err=True)
        raise typer.Exit(3) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Sync error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(json.dumps(asdict(report)))


@app.command()
def cost(config: ConfigOption = Path("lodestone.toml")) -> None:
    """Summarise llm_log rows per operation using the configured price table."""
    cfg = configuration(config)
    try:
        typer.echo(json.dumps(cost_workspace(cfg), indent=2))
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Cost error: {exc}", err=True)
        raise typer.Exit(1) from None


@app.command("get")
def get_record_cmd(
    ref: Annotated[str, typer.Argument(help="Record id or ext_id.")],
    config: ConfigOption = Path("lodestone.toml"),
    source: Annotated[str | None, typer.Option()] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Return raw text beside the stored card so claims stay checkable."""
    cfg = configuration(config)
    try:
        view = get_workspace(cfg, ref, source)
    except KeyError as exc:
        typer.echo(f"Get error: {exc}", err=True)
        raise typer.Exit(1) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Get error: {exc}", err=True)
        raise typer.Exit(1) from None
    if json_output:
        typer.echo(json.dumps(view, indent=2))
        return
    typer.echo(str(view["raw_text"]))
    if view["card"] is not None:
        typer.echo(json.dumps(view["card"], indent=2))


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Words, quoted phrases or trailing prefix *. ")],
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
    lane: Annotated[LaneName, typer.Option(help="Select one lexical lane.")] = "fts_raw",
    source: Annotated[list[str] | None, typer.Option(help="Source name; repeatable.")] = None,
    kind: Annotated[list[str] | None, typer.Option(help="Record kind; repeatable.")] = None,
    limit: Annotated[int, typer.Option(min=1)] = 10,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search a single lexical lane, with source/kind filters applied in SQL."""
    cfg = configuration(config)
    try:
        hits = search_workspace(
            cfg, query, project=project, lane=lane, sources=source, kinds=kind, limit=limit
        )
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Search error: {exc}", err=True)
        raise typer.Exit(1) from None
    if json_output:
        typer.echo(json.dumps({"lane": lane, "hits": [asdict(hit) for hit in hits]}))
    elif not hits:
        typer.echo("No matches.")
    else:
        for rank, hit in enumerate(hits, start=1):
            typer.echo(f"{rank}. {hit.source}/{hit.ext_id} [{hit.kind}] ({lane}, {hit.score:.6f})")
            typer.echo(f"   {hit.snippet}")


@source_app.command("add")
def source_add(
    name: Annotated[str, typer.Argument()],
    path: Annotated[Path, typer.Option("--path")],
    kind: Annotated[Literal["files", "threads"], typer.Option()] = "files",
    include: Annotated[list[str] | None, typer.Option()] = None,
    exclude: Annotated[list[str] | None, typer.Option()] = None,
    max_file_bytes: Annotated[int, typer.Option(min=1)] = 1024 * 1024,
    project: Annotated[str | None, typer.Option()] = None,
    config: ConfigOption = Path("lodestone.toml"),
) -> None:
    """Register a files or threads source and include it in the selected project."""
    configuration(config)
    try:
        from lodestone.connectors.files import validate_patterns

        validate_patterns((include or []) + (exclude or []))
        if kind == "files" and not path.is_dir():
            raise ValueError("files source path must be a directory")
        if kind == "threads" and not path.is_file():
            raise ValueError("threads source path must be a file")
        try:
            relative = Path(os.path.relpath(path.resolve(), config.resolve().parent))
        except ValueError:
            relative = path.resolve()
        source = Source(
            name=name,
            kind=kind,
            path=relative,
            include=include or [],
            exclude=exclude or [],
            max_file_bytes=max_file_bytes,
        )
        update_source(config, name, source=source, project=project)
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Source error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Added source: {name}")


@source_app.command("list")
def sources_list(
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
) -> None:
    """List sources in the selected project as JSON."""
    cfg = configuration(config)
    try:
        typer.echo(json.dumps(source_list(cfg, project)))
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None


@source_app.command("remove")
def source_remove(
    name: Annotated[str, typer.Argument()],
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Remove a source, its memberships and all indexed records and derived data."""
    configuration(config)
    try:
        update_source(config, name, project=project)
    except ValueError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    except (OSError, sqlite3.Error, StorageError) as exc:
        typer.echo(f"Source error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Removed source: {name}")


@source_app.command("sync")
def source_sync(
    name: Annotated[str | None, typer.Argument()] = None,
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
    prune: Annotated[bool, typer.Option()] = False,
    provider: Annotated[str | None, typer.Option()] = None,
    refresh_cards: Annotated[bool, typer.Option("--refresh-cards")] = False,
) -> None:
    """Sync one source, or all sources in the selected project."""
    sync(
        config=config,
        project=project,
        source=[name] if name is not None else None,
        prune=prune,
        provider=provider,
        refresh_cards=refresh_cards,
    )
