# SPDX-License-Identifier: Apache-2.0
"""Typer subcommands for lodestone bench synth, run, and report."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lodestone.bench.evalset import EvalsetError
from lodestone.bench.report import write_report
from lodestone.bench.runner import run_bench
from lodestone.bench.synth import generate

bench_app = typer.Typer(no_args_is_help=True, help="Offline RAG-strategy benchmark.")


def _fail(action: str, extra: BaseException) -> None:
    typer.echo(f"{action} error: {extra}", err=True)
    raise typer.Exit(1) from None


@bench_app.command("synth")
def synth_cmd(
    seed: Annotated[int, typer.Option("--seed")] = 42,
    threads: Annotated[int, typer.Option("--threads", min=1)] = 300,
    out: Annotated[Path, typer.Option("--out")] = Path("./bench/synth"),
) -> None:
    """Emit a deterministic synthetic corpus and evalset.v1 JSONL."""
    try:
        result = generate(out, seed=seed, threads=threads)
    except ValueError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None
    except OSError as extra:
        _fail("Synth", extra)
    typer.echo(f"wrote {result.questions} questions to {result.evalset}")
    typer.echo(f"corpus_hash {result.corpus_hash}")


@bench_app.command("run")
def run_cmd(
    corpus: Annotated[Path, typer.Option("--corpus")],
    out: Annotated[Path, typer.Option("--out")],
    evalset: Annotated[Path | None, typer.Option("--evalset")] = None,
    strategies: Annotated[str, typer.Option("--strategies")] = "all",
    k: Annotated[int, typer.Option("--k", min=1)] = 20,
) -> None:
    """Validate evalset.v1, run strategies offline, and write report files."""
    eval_path = evalset or (corpus / "evalset.jsonl")
    try:
        run = run_bench(corpus=corpus, evalset=eval_path, out=out, strategies=strategies, k=k)
        write_report(out, run=asdict(run))
    except EvalsetError as extra:
        typer.echo(str(extra), err=True)
        raise typer.Exit(2) from None
    except ValueError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None
    except OSError as extra:
        _fail("Bench", extra)
    typer.echo(f"wrote {out / 'report.md'}")


@bench_app.command("report")
def report_cmd(run_dir: Annotated[Path, typer.Argument()]) -> None:
    """Render report.md and report.json from a previous run directory."""
    try:
        markdown_path, _payload = write_report(run_dir)
    except (OSError, ValueError, KeyError) as extra:
        _fail("Report", extra)
    typer.echo(str(markdown_path))
