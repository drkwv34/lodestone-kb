# SPDX-License-Identifier: Apache-2.0
"""Deterministic advise rules R1-R4 over a bench report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EMBEDDING = ("classic-rag", "hybrid-chunks", "lodestone-hybrid", "lodestone-rerank")
CARDS = "lodestone-lexical"
BASELINE = "classic-rag"
PP = 0.03
CARD_CATEGORIES = ("paraphrase", "tangent_in_long_thread")

R1_VERDICT = "embeddings do not pay for themselves on this corpus"
R2_VERDICT = "consider context stuffing + caching"
R3_VERDICT = "distillation helps"
R4_VERDICT = "hybrid default"


@dataclass
class Advice:
    verdict: str
    rule: str
    evidence: list[str] = field(default_factory=list)

    def dump(self) -> dict[str, object]:
        return {"verdict": self.verdict, "rule": self.rule, "evidence": list(self.evidence)}

    def render(self) -> str:
        lines = [f"verdict: {self.verdict}", f"rule: {self.rule}", "evidence:"]
        lines.extend(f"- {item}" for item in self.evidence)
        return "\n".join(lines) + "\n"


def _metric(item: dict[str, Any], key: str) -> float | None:
    metrics = item.get("metrics")
    blob = metrics if isinstance(metrics, dict) else item
    value = blob.get(key)
    if value is None:
        value = item.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ci(item: dict[str, Any], key: str) -> tuple[float, float] | None:
    lo = item.get(f"{key}_lo")
    hi = item.get(f"{key}_hi")
    nested = item.get(f"{key}_ci")
    if isinstance(nested, (list, tuple)) and len(nested) == 2:
        lo, hi = nested[0], nested[1]
    stats = item.get("ci")
    if isinstance(stats, dict) and key in stats:
        payload = stats[key]
        if isinstance(payload, dict):
            lo = payload.get("lo", lo)
            hi = payload.get("hi", hi)
    if lo is None or hi is None:
        return None
    return float(lo), float(hi)


def _ok(item: dict[str, Any] | None) -> bool:
    return item is not None and item.get("status") == "ok"


def _by_name(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): item for item in report.get("strategies") or [] if "name" in item}


def _paired(report: dict[str, Any], name: str, metric: str) -> dict[str, Any] | None:
    paired = report.get("paired") or {}
    block = paired.get(name) if isinstance(paired, dict) else None
    if not isinstance(block, dict):
        return None
    inner = block.get(metric, block)
    return inner if isinstance(inner, dict) else None


def report_costs(report_or_item: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report_or_item.get("cost_latency")
    return list(rows) if isinstance(rows, list) else []


def _cost_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = {str(row.get("strategy")): row for row in report_costs(report)}
    for name, item in _by_name(report).items():
        mapping.setdefault(name, item)
    return mapping


def _per_query(report: dict[str, Any], name: str) -> float | None:
    row = _cost_map(report).get(name)
    if row is None:
        return None
    usd = row.get("usd")
    queries = row.get("queries") or _by_name(report).get(name, {}).get("queries") or 1
    if usd is None:
        return None
    return float(usd) / max(1, int(queries))


def _best_embedding(strategies: dict[str, dict[str, Any]]) -> tuple[str, float] | None:
    best: tuple[str, float] | None = None
    for name in EMBEDDING:
        item = strategies.get(name)
        if not _ok(item):
            continue
        score = _metric(item, "recall@10")  # type: ignore[arg-type]
        if score is None:
            continue
        if best is None or score > best[1]:
            best = (name, score)
    return best


def _rule_r1(strategies: dict[str, dict[str, Any]], report: dict[str, Any]) -> list[str] | None:
    lexical = strategies.get(CARDS)
    if not _ok(lexical):
        return None
    lexical_r10 = _metric(lexical, "recall@10")  # type: ignore[arg-type]
    best = _best_embedding(strategies)
    if lexical_r10 is None or best is None:
        return None
    embed_name, embed_r10 = best
    delta = abs(lexical_r10 - embed_r10)
    paired = _paired(report, CARDS, "recall@10") or {}
    lo = paired.get("lo")
    hi = paired.get("hi")
    includes_zero = True if lo is None or hi is None else float(lo) <= 0.0 <= float(hi)
    if delta <= PP and includes_zero:
        return [
            f"{CARDS} recall@10={lexical_r10:.4f}",
            f"best embedding {embed_name} recall@10={embed_r10:.4f}",
            f"|delta|={delta:.4f} pp-limit={PP}",
            f"paired CI includes 0: {includes_zero} lo={lo} hi={hi}",
        ]
    return None


def _rule_r2(strategies: dict[str, dict[str, Any]], report: dict[str, Any]) -> list[str] | None:
    full = strategies.get("full-context")
    if not _ok(full):
        return None
    fc_corr = _metric(full, "correctness")  # type: ignore[arg-type]
    fc_ci = _ci(full, "correctness")  # type: ignore[arg-type]
    best_name = None
    best_corr: float | None = None
    for name, item in strategies.items():
        if name == "full-context" or not _ok(item):
            continue
        score = _metric(item, "correctness")
        if score is None:
            continue
        if best_corr is None or score > best_corr:
            best_corr = score
            best_name = name
    if fc_corr is None or best_corr is None or best_name is None:
        return None
    fc_lo = fc_ci[0] if fc_ci is not None else fc_corr
    if fc_lo < best_corr:
        return None
    fc_cost = _per_query(report, "full-context")
    other_cost = _per_query(report, best_name)
    if fc_cost is None or other_cost is None:
        return None
    ratio_ok = fc_cost <= 0 if other_cost <= 0 else fc_cost <= 3 * other_cost
    if not ratio_ok:
        return None
    status = str(full.get("status") if full is not None else "")
    return [
        f"full-context feasible status={status}",
        f"full-context correctness CI lo={fc_lo:.4f} >= {best_name} correctness={best_corr:.4f}",
        f"full-context cost/query={fc_cost:.6f} vs 3x {best_name}={3 * other_cost:.6f}",
    ]


def _category_score(report: dict[str, Any], strategy: str, category: str) -> float | None:
    for row in report.get("categories") or []:
        if row.get("strategy") == strategy and row.get("category") == category:
            value = row.get("recall@10")
            if value is None:
                continue
            return float(value)
    item = _by_name(report).get(strategy)
    by_category = (item or {}).get("by_category") or {}
    scores = by_category.get(category) or {}
    value = scores.get("recall@10")
    return float(value) if value is not None else None


def _rule_r3(strategies: dict[str, dict[str, Any]], report: dict[str, Any]) -> list[str] | None:
    if not _ok(strategies.get(CARDS)) or not _ok(strategies.get(BASELINE)):
        return None
    paired_cat = report.get("category_paired") or {}
    evidence: list[str] = []
    for category in CARD_CATEGORIES:
        cards = _category_score(report, CARDS, category)
        baseline = _category_score(report, BASELINE, category)
        block = paired_cat.get(category) if isinstance(paired_cat, dict) else None
        significant = bool(block.get("significant")) if isinstance(block, dict) else False
        if cards is None or baseline is None:
            continue
        if cards > baseline and significant:
            evidence.append(
                f"{CARDS} {category} recall@10={cards:.4f} > {BASELINE}={baseline:.4f} significant"
            )
    if evidence:
        return evidence
    return None


def advise(report: dict[str, Any]) -> Advice:
    strategies = _by_name(report)
    matched = _rule_r1(strategies, report)
    if matched is not None:
        return Advice(R1_VERDICT, "R1", matched)
    matched = _rule_r2(strategies, report)
    if matched is not None:
        return Advice(R2_VERDICT, "R2", matched)
    matched = _rule_r3(strategies, report)
    if matched is not None:
        return Advice(R3_VERDICT, "R3", matched)
    evidence = ["no R1-R3 match; default hybrid retrieval"]
    lexical = strategies.get(CARDS)
    if lexical is not None:
        score = _metric(lexical, "recall@10")
        if score is not None:
            evidence.append(f"{CARDS} recall@10={score:.4f}")
    return Advice(R4_VERDICT, "R4", evidence)
