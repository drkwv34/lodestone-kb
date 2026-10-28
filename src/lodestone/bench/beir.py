# SPDX-License-Identifier: Apache-2.0
"""BEIR-format adapter for lodestone bench import (FR-079)."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from lodestone.bench.evalset import EvalRow

SCIFACT_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
SCIFACT_MD5 = "5f7d1de60b170fc8027bb7898e2efca1"
SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")
Fetch = Callable[[str], bytes]


class BeirError(ValueError):
    """Invalid BEIR spec, files, or checksum."""


@dataclass(frozen=True)
class ImportResult:
    directory: Path
    evalset: Path
    documents: int
    questions: int
    dataset: str


def parse_spec(spec: str) -> str:
    text = spec.strip().lower()
    if text.startswith("beir:"):
        text = text[5:]
    if text != "scifact":
        raise BeirError(f"unsupported BEIR dataset {spec!r}; expected beir:scifact")
    return "scifact"


def sanitise_id(ident: str) -> str:
    cleaned = SAFE_ID.sub("_", ident.strip()).strip("._-")
    return (cleaned or "doc")[:120]


def md5_digest(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def http_get(url: str) -> bytes:
    try:
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as extra:
        raise BeirError(f"download failed: {extra}") from extra


def download_scifact(fetch: Fetch | None = None) -> bytes:
    data = (fetch or http_get)(SCIFACT_URL)
    digest = md5_digest(data)
    if digest != SCIFACT_MD5:
        raise BeirError(f"checksum mismatch for scifact.zip: expected {SCIFACT_MD5}, got {digest}")
    return data


def _extract_zip(data: bytes, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "dataset.zip"
    zip_path.write_bytes(data)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(dest)
    except zipfile.BadZipFile as extra:
        raise BeirError("archive is not a valid zip") from extra
    return dest


def find_dataset_root(root: Path) -> Path:
    candidates = [root]
    if (root / "scifact").is_dir():
        candidates.append(root / "scifact")
    candidates.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    for candidate in candidates:
        if (candidate / "corpus.jsonl").is_file() and (candidate / "queries.jsonl").is_file():
            return candidate
    raise BeirError("BEIR directory must contain corpus.jsonl and queries.jsonl")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as extra:
            raise BeirError(f"{path.name} line {line}: invalid JSON") from extra
        if not isinstance(payload, dict):
            raise BeirError(f"{path.name} line {line}: expected object")
        rows.append(payload)
    if not rows:
        raise BeirError(f"{path.name} is empty")
    return rows


def _qrels(path: Path) -> dict[str, list[str]]:
    gold: dict[str, list[str]] = {}
    for line, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith("query-id") or lowered.startswith("qid"):
            continue
        parts = stripped.replace(",", "\t").split()
        if len(parts) == 4:
            qid, _iteration, doc_id, score = parts
        elif len(parts) == 3:
            qid, doc_id, score = parts
        else:
            raise BeirError(f"{path.name} line {line}: expected 3 or 4 columns")
        try:
            relevant = float(score)
        except ValueError as extra:
            raise BeirError(f"{path.name} line {line}: invalid score") from extra
        if relevant <= 0:
            continue
        bucket = gold.setdefault(qid, [])
        if doc_id not in bucket:
            bucket.append(doc_id)
    return gold


def _qrels_from_root(root: Path) -> dict[str, list[str]]:
    qrels_dir = root / "qrels"
    files: list[Path] = []
    if qrels_dir.is_dir():
        preferred = qrels_dir / "test.tsv"
        files = [preferred] if preferred.is_file() else sorted(qrels_dir.glob("*.tsv"))
    elif (root / "qrels.tsv").is_file():
        files = [root / "qrels.tsv"]
    gold: dict[str, list[str]] = {}
    for path in files:
        for qid, docs in _qrels(path).items():
            bucket = gold.setdefault(qid, [])
            for doc_id in docs:
                if doc_id not in bucket:
                    bucket.append(doc_id)
    return gold


def _unique_relative(used: set[str], ident: str) -> str:
    base = sanitise_id(ident)
    relative = f"docs/{base}.md"
    suffix = 2
    while relative in used:
        relative = f"docs/{base}-{suffix}.md"
        suffix += 1
    used.add(relative)
    return relative


def convert_beir(root: Path, out: Path) -> ImportResult:
    dataset_root = find_dataset_root(root)
    corpus = _load_jsonl(dataset_root / "corpus.jsonl")
    queries = _load_jsonl(dataset_root / "queries.jsonl")
    qrels = _qrels_from_root(dataset_root)
    docs_dir = out / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    id_to_ext: dict[str, str] = {}
    for row in corpus:
        ident = str(row.get("_id") or "").strip()
        if not ident:
            raise BeirError("corpus row missing _id")
        title = str(row.get("title") or ident)
        text = str(row.get("text") or "")
        relative = _unique_relative(used, ident)
        heading = title.strip() or ident
        body = f"# {heading}\n\n{text.strip()}\n"
        (out / relative).write_text(body, encoding="utf-8", newline="\n")
        id_to_ext[ident] = relative
    rows: list[EvalRow] = []
    for row in queries:
        qid = str(row.get("_id") or "").strip()
        question = str(row.get("text") or "").strip()
        if not qid or not question:
            raise BeirError("query row missing _id or text")
        gold_ids = [id_to_ext[doc] for doc in qrels.get(qid, []) if doc in id_to_ext]
        rows.append(
            EvalRow(
                qid=qid,
                question=question,
                gold_ids=gold_ids,
                category="paraphrase" if gold_ids else "unanswerable",
                source_hint="beir:scifact",
            )
        )
    eval_path = out / "evalset.jsonl"
    payload = "\n".join(
        json.dumps(item.dump(), ensure_ascii=True, separators=(",", ":")) for item in rows
    )
    eval_path.write_text(payload + ("\n" if rows else ""), encoding="utf-8", newline="\n")
    return ImportResult(
        directory=out,
        evalset=eval_path,
        documents=len(id_to_ext),
        questions=len(rows),
        dataset="scifact",
    )


def import_beir(
    spec: str,
    out: Path,
    *,
    source: Path | None = None,
    fetch: Fetch | None = None,
) -> ImportResult:
    parse_spec(spec)
    out.mkdir(parents=True, exist_ok=True)
    if source is None:
        data = download_scifact(fetch)
        with tempfile.TemporaryDirectory() as tmp:
            extracted = _extract_zip(data, Path(tmp))
            return convert_beir(extracted, out)
    if not source.exists():
        raise BeirError(f"BEIR source not found: {source}")
    if source.is_dir():
        return convert_beir(source, out)
    if source.is_file() and source.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmp:
            extracted = _extract_zip(source.read_bytes(), Path(tmp))
            return convert_beir(extracted, out)
    raise BeirError("BEIR --from must be a directory or zip")
