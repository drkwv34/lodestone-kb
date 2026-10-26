# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from lodestone.bench.evalset import CATEGORIES
from lodestone.bench.report import HASH_CAVEAT, render_markdown, report_payload, write_report
from lodestone.bench.schema import load_schema

FIXTURE = Path(__file__).parents[1] / "fixtures/bench/report.md"


def _run() -> dict[str, object]:
    metrics = {
        "recall@1": 0.5,
        "recall@5": 1.0,
        "recall@10": 1.0,
        "recall@20": 1.0,
        "mrr": 0.5,
        "ndcg@10": 0.693426,
    }
    per_category = {
        category: {"recall@10": 1.0, "mrr": 1.0, "ndcg@10": 1.0} for category in CATEGORIES
    }
    return {
        "generated_at": "2026-01-02T00:00:00+00:00",
        "config_hash": "aa" * 32,
        "corpus_hash": "bb" * 32,
        "versions": {"lodestone": "0.1.0.dev0"},
        "embedder": "hash",
        "strategies": [
            {
                "name": "classic-rag",
                "status": "ok",
                "skipped_reason": None,
                "metrics": metrics,
                "by_category": per_category,
                "index_seconds": 1.25,
                "index_bytes": 4096,
                "in_tokens": 0,
                "out_tokens": 0,
                "usd": 0.0,
                "p50_ms": 1.0,
                "p95_ms": 2.0,
                "p99_ms": 3.0,
            },
            {
                "name": "lodestone-hybrid",
                "status": "skipped",
                "skipped_reason": "not implemented in this change",
                "metrics": {},
                "by_category": {},
                "index_seconds": 0.0,
                "index_bytes": 0,
                "in_tokens": 0,
                "out_tokens": 0,
                "usd": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
            },
        ],
        "failures": [],
    }


def test_fr_076_hash_embedder_caveat() -> None:
    payload = report_payload(_run())
    assert HASH_CAVEAT in payload["caveats"]
    markdown = render_markdown(payload)
    assert HASH_CAVEAT in markdown


def test_fr_076_report_golden_stable(tmp_path: Path) -> None:
    schema = load_schema("report.v1.json")
    assert schema["title"] == "report.v1"
    payload = report_payload(_run(), generated_at="2026-01-02T00:00:00+00:00")
    markdown = render_markdown(payload)
    expected = FIXTURE.read_text(encoding="utf-8")
    assert markdown == expected
    body = "\n".join(markdown.splitlines()[2:])
    assert "2026-01-02T00:00:00+00:00" not in body
    assert markdown.splitlines()[1] == "Generated: 2026-01-02T00:00:00+00:00"
    write_report(tmp_path, run=_run(), generated_at="2026-01-02T00:00:00+00:00")
    assert (tmp_path / "report.md").read_text(encoding="utf-8") == expected
    assert (tmp_path / "report.json").is_file()
