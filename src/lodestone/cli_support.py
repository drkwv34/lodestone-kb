# SPDX-License-Identifier: Apache-2.0
"""Shared CLI config loading and exit-code mapping."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lodestone.config import Config, ConfigError, load_config
from lodestone.providers import OfflineError, ProviderError
from lodestone.storage.db import StorageError

ConfigOption = Annotated[Path, typer.Option("--config", "-c", help="Path to lodestone.toml.")]

Caught = (
    ConfigError,
    ValueError,
    ProviderError,
    OfflineError,
    OSError,
    sqlite3.Error,
    StorageError,
    KeyError,
)


def configuration(path: Path) -> Config:
    try:
        return load_config(path)
    except ConfigError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None


def fail(action: str, exc: BaseException) -> None:
    if isinstance(exc, (ConfigError, ValueError)):
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(2) from None
    if isinstance(exc, (ProviderError, OfflineError)):
        typer.echo(f"Provider error: {exc}", err=True)
        raise typer.Exit(3) from None
    typer.echo(f"{action} error: {exc}", err=True)
    raise typer.Exit(1) from None


def mcp_command(
    config: ConfigOption = Path("lodestone.toml"),
    offline: Annotated[bool, typer.Option("--offline")] = False,
) -> None:
    """Run the read-only MCP stdio server."""
    from lodestone.mcp_server import run_stdio

    try:
        run_stdio(configuration(config), offline=offline)
    except Caught as extra:
        fail("MCP", extra)


def ask_command(
    question: Annotated[str, typer.Argument()],
    config: ConfigOption = Path("lodestone.toml"),
    project: Annotated[str | None, typer.Option()] = None,
    max_rounds: Annotated[int | None, typer.Option("--max-rounds")] = None,
    provider: Annotated[str | None, typer.Option(help="fake or config.")] = None,
    offline: Annotated[bool, typer.Option("--offline")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Answer a question with citations from retrieved evidence."""
    from lodestone.sdk import Lodestone

    try:
        answer = Lodestone(configuration(config), offline=offline).ask(
            question, project=project, max_rounds=max_rounds, provider=provider
        )
    except Caught as extra:
        fail("Ask", extra)
    if json_output:
        typer.echo(json.dumps(asdict(answer), indent=2))
        return
    typer.echo(answer.text)
    if answer.insufficient_evidence:
        typer.echo("insufficient_evidence: true")
