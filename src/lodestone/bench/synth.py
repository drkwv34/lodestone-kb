# SPDX-License-Identifier: Apache-2.0
"""Deterministic synthetic corpus and evalset for the offline benchmark."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lodestone.bench.evalset import CATEGORIES, EvalRow

AUTHORS = ("maya", "owen", "ravi", "lina")
EPOCH = datetime(2026, 1, 1, tzinfo=UTC)
CHANNEL = "synth-support"
FILLER = "sounds good, thanks! we can look later at the dashboard graphs."


@dataclass(frozen=True)
class SynthResult:
    directory: Path
    evalset: Path
    corpus_hash: str
    questions: int
    threads: int


def file_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _write(path: Path, text: str, when: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    stamp = when.timestamp()
    os.utime(path, (stamp, stamp))


def _iso(when: datetime) -> str:
    return when.astimezone(UTC).isoformat()


def _token(seed: int, index: int) -> str:
    return f"ERR_SYNTH_{seed:04d}_{index:04d}"


def _ckpt(seed: int, index: int) -> str:
    return f"CKPT_SYNTH_{seed:04d}_{index:04d}"


def _message(
    ident: str, author: str, when: datetime, text: str, reactions: int = 0
) -> dict[str, object]:
    return {
        "id": ident,
        "author": author,
        "ts": _iso(when),
        "text": text,
        "reactions": reactions,
    }


def _thread(thread_id: str, title: str, messages: list[dict[str, object]]) -> dict[str, object]:
    return {
        "thread_id": thread_id,
        "channel": CHANNEL,
        "title": title,
        "messages": messages,
    }


def _dump(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def generate(directory: Path, *, seed: int, threads: int) -> SynthResult:
    if threads < 1:
        raise ValueError("threads must be positive")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "docs").mkdir(exist_ok=True)
    (directory / "code").mkdir(exist_ok=True)
    thread_lines: list[str] = []
    questions: list[EvalRow] = []
    for index in range(threads):
        category = CATEGORIES[index % len(CATEGORIES)]
        when = EPOCH + timedelta(days=index)
        author = AUTHORS[index % len(AUTHORS)]
        token = _token(seed, index)
        flag = _ckpt(seed, index)
        thread_id = f"thread-{index:04d}"
        files, thread, rows = _slot(
            category,
            index=index,
            seed=seed,
            token=token,
            flag=flag,
            thread_id=thread_id,
            when=when,
            author=author,
        )
        for relative, body, stamp in files:
            _write(directory / relative, body, stamp)
        thread_lines.append(_dump(thread))
        questions.extend(rows)
    _write(directory / "threads.jsonl", "\n".join(thread_lines) + "\n", EPOCH)
    eval_path = directory / "evalset.jsonl"
    _write(
        eval_path,
        "\n".join(_dump(row.dump()) for row in questions) + "\n",
        EPOCH,
    )
    return SynthResult(
        directory=directory,
        evalset=eval_path,
        corpus_hash=file_tree_hash(directory),
        questions=len(questions),
        threads=threads,
    )


def _slot(
    category: str,
    *,
    index: int,
    seed: int,
    token: str,
    flag: str,
    thread_id: str,
    when: datetime,
    author: str,
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    if category == "exact_token":
        return _exact(index, token, thread_id, when, author)
    if category == "paraphrase":
        return _paraphrase(index, flag, thread_id, when, author)
    if category == "stale_vs_fresh":
        return _stale(index, flag, thread_id, when, author)
    if category == "tangent_in_long_thread":
        return _tangent(index, token, thread_id, when, author)
    if category == "multi_source":
        return _multi(index, flag, thread_id, when, author)
    return _unanswerable(index, seed, thread_id, when, author)


def _exact(
    index: int, token: str, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    doc = f"docs/exact_{index:04d}.md"
    code = f"code/exact_{index:04d}.py"
    files = [
        (
            doc,
            f"# {token}\n\n{token} is raised when the manifest checksum mismatches.\n",
            when,
        ),
        (
            code,
            f"# {token}: manifest checksum mismatch\n"
            f"def restore():\n    raise RuntimeError({token!r})\n",
            when,
        ),
    ]
    thread = _thread(
        thread_id,
        f"{token} on restore",
        [_message(f"{thread_id}-m0", author, when, f"We hit {token} after the manifest load.")],
    )
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-exact",
            question=f"What raises {token}?",
            gold_ids=[doc],
            category="exact_token",
            gold_answer_must_contain=["manifest checksum"],
            source_hint=doc,
        )
    ]
    return files, thread, rows


def _paraphrase(
    index: int, flag: str, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    doc = f"docs/para_{index:04d}.md"
    files = [
        (
            doc,
            "# Checkpoint restore on NFS\n\n"
            "The restore job finishes after setting prefetch to four on NFS mounts "
            f"using {flag}.\n",
            when,
        )
    ]
    thread = _thread(
        thread_id,
        "restore hang",
        [_message(f"{thread_id}-m0", author, when, "The hang goes away once prefetch is four.")],
    )
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-para",
            question="How do I stop the restore hang on the network filesystem?",
            gold_ids=[doc],
            category="paraphrase",
            gold_answer_must_contain=["prefetch to four"],
            source_hint=doc,
        )
    ]
    return files, thread, rows


def _stale(
    index: int, flag: str, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    stale_when = when - timedelta(days=180)
    fresh_when = when
    stale = f"docs/stale_{index:04d}.md"
    fresh = f"docs/fresh_{index:04d}.md"
    files = [
        (
            stale,
            f"# Old prefetch guidance\n\nSet {flag}=1; anything higher crashes the agent.\n",
            stale_when,
        ),
        (
            fresh,
            f"# Current prefetch guidance\n\nSet {flag}=4 so restore completes on NFS.\n",
            fresh_when,
        ),
    ]
    thread = _thread(
        thread_id,
        f"{flag} prefetch",
        [
            _message(
                f"{thread_id}-m0", author, stale_when, f"Still using {flag}=1 from last year."
            ),
            _message(
                f"{thread_id}-m1",
                AUTHORS[(index + 1) % 4],
                fresh_when,
                f"Update: {flag}=4 is the current value.",
            ),
        ],
    )
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-fresh",
            question=f"What prefetch value should I use for {flag}?",
            gold_ids=[fresh],
            category="stale_vs_fresh",
            gold_answer_must_contain=["4"],
            source_hint=fresh,
        )
    ]
    return files, thread, rows


def _tangent(
    index: int, token: str, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    messages = []
    for step in range(48):
        stamp = when + timedelta(minutes=step)
        who = AUTHORS[(index + step) % 4]
        text = FILLER if step != 31 else f"the timeout is {token} on the NFS path"
        messages.append(_message(f"{thread_id}-m{step:02d}", who, stamp, text))
    thread = _thread(thread_id, "long restore chat", messages)
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-tangent",
            question=f"What timeout appears on the NFS path for {token}?",
            gold_ids=[thread_id],
            category="tangent_in_long_thread",
            gold_answer_must_contain=[token],
            source_hint=thread_id,
        )
    ]
    return [], thread, rows


def _multi(
    index: int, flag: str, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    doc = f"docs/multi_{index:04d}.md"
    files = [
        (
            doc,
            f"# Flag name\n\nThe restore finish flag is named {flag}.\n",
            when,
        )
    ]
    thread = _thread(
        thread_id,
        f"set {flag}",
        [_message(f"{thread_id}-m0", author, when, f"Set {flag} to 4 to finish restore.")],
    )
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-multi",
            question=f"How do I finish restore using {flag}?",
            gold_ids=[doc, thread_id],
            category="multi_source",
            gold_answer_must_contain=["4"],
            source_hint=doc,
        )
    ]
    return files, thread, rows


def _unanswerable(
    index: int, seed: int, thread_id: str, when: datetime, author: str
) -> tuple[list[tuple[str, str, datetime]], dict[str, object], list[EvalRow]]:
    thread = _thread(
        thread_id,
        "lunch plans",
        [_message(f"{thread_id}-m0", author, when, "Anyone free for lunch near the south campus?")],
    )
    rows = [
        EvalRow(
            qid=f"q-{index:04d}-none",
            question=f"What is the capital of Atlantis in seed {seed} case {index:04d}?",
            gold_ids=[],
            category="unanswerable",
        )
    ]
    return [], thread, rows
