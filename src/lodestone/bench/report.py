# SPDX-License-Identifier: Apache-2.0
"""report.v1 markdown and JSON skeleton with a stable body (header timestamp only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lodestone.bench.evalset import CATEGORIES
from lodestone.bench.runner import load_run
from lodestone.bench.schema import load_schema

HASH_CAVEAT = "hash embedder is not semantic"
METRIC_KEYS = ("recall@1", "recall@5", "recall@10", "recall@20", "mrr", "ndcg@10")


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _row(cells: list[object]) -> str:
    return "| " + " | ".join(_cell(item) for item in cells) + " |"


def caveats_for(run: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    embedder = str(run.get("embedder") or "")
    if embedder == "hash":
        notes.append(HASH_CAVEAT)
    skipped = [
        f"{item['name']} skipped: {item.get('skipped_reason') or 'unspecified'}"
        for item in run.get("strategies", [])
        if item.get("status") == "skipped"
    ]
    notes.extend(skipped)
    leakage = run.get("leakage") or {}
    histogram = leakage.get("histogram") if isinstance(leakage, dict) else None
    if not histogram:
        notes.append("leakage stats are a placeholder until real-corpus question generation")
    return notes


def report_payload(run: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    stamp = generated_at or str(run.get("generated_at") or "")
    strategies = []
    categories = []
    cost_latency = []
    for item in run.get("strategies", []):
        metrics = item.get("metrics") or {}
        strategies.append(
            {
                "name": item["name"],
                "status": item.get("status"),
                "skipped_reason": item.get("skipped_reason"),
                **{key: metrics.get(key) for key in METRIC_KEYS},
                "correctness": metrics.get("correctness"),
                "correctness_lo": metrics.get("correctness_lo"),
                "correctness_hi": metrics.get("correctness_hi"),
                "recall@10_lo": metrics.get("recall@10_lo"),
                "recall@10_hi": metrics.get("recall@10_hi"),
                "index_seconds": item.get("index_seconds", 0.0),
                "index_bytes": item.get("index_bytes", 0),
                "usd": item.get("usd", 0.0),
                "queries": item.get("queries", 0),
            }
        )
        by_category = item.get("by_category") or {}
        for category in CATEGORIES:
            scores = by_category.get(category) or {}
            categories.append(
                {
                    "strategy": item["name"],
                    "category": category,
                    "recall@10": scores.get("recall@10"),
                    "mrr": scores.get("mrr"),
                    "ndcg@10": scores.get("ndcg@10"),
                }
            )
        cost_latency.append(
            {
                "strategy": item["name"],
                "in_tokens": item.get("in_tokens", 0),
                "out_tokens": item.get("out_tokens", 0),
                "usd": item.get("usd", 0.0),
                "p50_ms": item.get("p50_ms", 0.0),
                "p95_ms": item.get("p95_ms", 0.0),
                "p99_ms": item.get("p99_ms", 0.0),
                "queries": item.get("queries", 0),
            }
        )
    leakage = run.get("leakage") if isinstance(run.get("leakage"), dict) else None
    payload = {
        "schema": "report.v1",
        "generated_at": stamp,
        "config_hash": run.get("config_hash", ""),
        "corpus_hash": run.get("corpus_hash", ""),
        "versions": run.get("versions") or {},
        "embedder": run.get("embedder", ""),
        "strategies": strategies,
        "categories": categories,
        "cost_latency": cost_latency,
        "leakage": leakage or {"dropped": 0, "histogram": []},
        "paired": run.get("paired") or {},
        "category_paired": run.get("category_paired") or {},
        "caveats": caveats_for(run),
        "failures": list(run.get("failures") or []),
    }
    spec = load_schema("report.v1.json")
    missing = [key for key in spec.get("required", []) if key not in payload]
    if missing:
        raise ValueError(f"report.v1 missing {missing}")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    versions = payload.get("versions") or {}
    lines = [
        "# Lodestone bench report",
        f"Generated: {payload['generated_at']}",
        "",
        "## Run",
        f"- config_hash: {payload['config_hash']}",
        f"- corpus_hash: {payload['corpus_hash']}",
        f"- lodestone: {versions.get('lodestone', '')}",
        f"- embedder: {payload.get('embedder', '')}",
        "",
        "## Strategies",
        _row(["strategy", "status", *METRIC_KEYS, "index_s", "index_bytes"]),
        _row(["---"] * 10),
    ]
    for item in payload["strategies"]:
        lines.append(
            _row(
                [
                    item["name"],
                    item.get("status"),
                    *[item.get(key) for key in METRIC_KEYS],
                    item.get("index_seconds"),
                    item.get("index_bytes"),
                ]
            )
        )
    lines.extend(
        [
            "",
            "## Per category",
            _row(["strategy", "category", "recall@10", "mrr", "ndcg@10"]),
            _row(["---"] * 5),
        ]
    )
    for item in payload["categories"]:
        lines.append(
            _row(
                [
                    item["strategy"],
                    item["category"],
                    item.get("recall@10"),
                    item.get("mrr"),
                    item.get("ndcg@10"),
                ]
            )
        )
    lines.extend(
        [
            "",
            "## Cost and latency",
            _row(["strategy", "in_tokens", "out_tokens", "usd", "p50_ms", "p95_ms", "p99_ms"]),
            _row(["---"] * 7),
        ]
    )
    for item in payload["cost_latency"]:
        lines.append(
            _row(
                [
                    item["strategy"],
                    item.get("in_tokens"),
                    item.get("out_tokens"),
                    item.get("usd"),
                    item.get("p50_ms"),
                    item.get("p95_ms"),
                    item.get("p99_ms"),
                ]
            )
        )
    leakage = payload.get("leakage") or {}
    histogram = leakage.get("histogram") or []
    hist_text = "none"
    if histogram:
        hist_text = "; ".join(
            f"{row.get('lo', 0):.1f}-{row.get('hi', 0):.1f}:{row.get('count', 0)}"
            for row in histogram
        )
    lines.extend(
        [
            "",
            "## Leakage",
            f"- dropped: {leakage.get('dropped', 0)}",
            f"- histogram: {hist_text}",
            "",
            "## Caveats",
        ]
    )
    for note in payload["caveats"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Failures"])
    failures = payload.get("failures") or []
    if failures:
        lines.extend(f"- {item}" for item in failures)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_report(
    run_dir: Path, *, generated_at: str | None = None, run: dict[str, Any] | None = None
) -> tuple[Path, Path]:
    payload_run = run if run is not None else load_run(run_dir / "results.json")
    payload = report_payload(payload_run, generated_at=generated_at)
    markdown = render_markdown(payload)
    md_path = run_dir / "report.md"
    json_path = run_dir / "report.json"
    md_path.write_text(markdown, encoding="utf-8", newline="\n")
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path
