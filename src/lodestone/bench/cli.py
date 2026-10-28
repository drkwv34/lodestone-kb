# SPDX-License-Identifier: Apache-2.0
"""Typer subcommands for lodestone bench synth, generate, run, report, advise, import."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lodestone.bench.advise import advise
from lodestone.bench.beir import BeirError, import_beir
from lodestone.bench.evalset import EvalsetError
from lodestone.bench.questions import DEFAULT_LEAKAGE_MAX, dump_evalset, generate_from_config
from lodestone.bench.report import write_report
from lodestone.bench.runner import load_run, run_bench
from lodestone.bench.strategies import DEFAULT_CONTEXT_BUDGET
from lodestone.bench.synth import generate
from lodestone.config import ConfigError, load_config
from lodestone.providers import FakeLLM, make_chat

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


@bench_app.command("generate")
def generate_cmd(
    corpus: Annotated[Path, typer.Option("--corpus", help="Path to lodestone.toml.")],
    out: Annotated[Path, typer.Option("--out")] = Path("evalset.jsonl"),
    n: Annotated[int, typer.Option("--n", min=1)] = 200,
    leakage_max: Annotated[float, typer.Option("--leakage-max")] = DEFAULT_LEAKAGE_MAX,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    provider: Annotated[str, typer.Option("--provider")] = "fake",
) -> None:
    """Sample workspace records and write leakage-filtered evalset.v1 JSONL."""
    try:
        config = load_config(corpus)
        chat = (
            FakeLLM() if provider == "fake" else make_chat(config, provider, offline=config.offline)
        )
        generated = generate_from_config(config, n=n, chat=chat, leakage_max=leakage_max, seed=seed)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dump_evalset(generated.rows), encoding="utf-8", newline="\n")
        leak_path = out.with_name("leakage.json")
        leak_path.write_text(
            json.dumps(generated.leakage.dump(), indent=2) + "\n", encoding="utf-8"
        )
    except ConfigError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None
    except ValueError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None
    except OSError as extra:
        _fail("Generate", extra)
    typer.echo(f"wrote {len(generated.rows)} questions to {out}")
    typer.echo(f"dropped {generated.leakage.dropped} leaking questions")


@bench_app.command("run")
def run_cmd(
    corpus: Annotated[Path, typer.Option("--corpus")],
    out: Annotated[Path, typer.Option("--out")],
    evalset: Annotated[Path | None, typer.Option("--evalset")] = None,
    strategies: Annotated[str, typer.Option("--strategies")] = "all",
    k: Annotated[int, typer.Option("--k", min=1)] = 20,
    judge: Annotated[bool, typer.Option("--judge")] = False,
    reps: Annotated[int, typer.Option("--reps", min=1)] = 1,
    context_budget: Annotated[
        int, typer.Option("--context-budget", min=1)
    ] = DEFAULT_CONTEXT_BUDGET,
) -> None:
    """Validate evalset.v1, run strategies offline, and write report files."""
    eval_path = evalset or (corpus / "evalset.jsonl")
    try:
        run = run_bench(
            corpus=corpus,
            evalset=eval_path,
            out=out,
            strategies=strategies,
            k=k,
            judge=judge,
            reps=reps,
            context_budget=context_budget,
        )
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


@bench_app.command("import")
def import_cmd(
    spec: Annotated[str, typer.Argument(help="beir:<dataset>, currently beir:scifact")],
    out: Annotated[Path, typer.Option("--out")],
    source: Annotated[
        Path | None,
        typer.Option("--from", help="Local BEIR directory or zip; skip the public download."),
    ] = None,
) -> None:
    """Convert a BEIR-format dataset into a Lodestone corpus and evalset.v1."""
    try:
        result = import_beir(spec, out, source=source)
    except BeirError as extra:
        typer.echo(f"Configuration error: {extra}", err=True)
        raise typer.Exit(2) from None
    except OSError as extra:
        _fail("Import", extra)
    typer.echo(f"wrote {result.questions} questions to {result.evalset}")
    typer.echo(f"documents {result.documents}")


@bench_app.command("advise")
def advise_cmd(run_dir: Annotated[Path, typer.Argument()]) -> None:
    """Emit a deterministic R1-R4 verdict from a bench report."""
    try:
        report_path = run_dir / "report.json"
        payload = (
            json.loads(report_path.read_text(encoding="utf-8"))
            if report_path.is_file()
            else load_run(run_dir / "results.json")
        )
        if not isinstance(payload, dict):
            raise ValueError("report.json must be an object")
        advice = advise(payload)
        text = advice.render()
        (run_dir / "advise.md").write_text(text, encoding="utf-8", newline="\n")
    except (OSError, ValueError, KeyError) as extra:
        _fail("Advise", extra)
    typer.echo(text, nl=False)
