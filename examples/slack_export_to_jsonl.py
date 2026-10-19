# SPDX-License-Identifier: Apache-2.0
"""Convert a Slack workspace export directory into FR-011 threads JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load_users(root: Path) -> dict[str, str]:
    path = root / "users.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return {}
    names: dict[str, str] = {}
    for user in payload:
        if not isinstance(user, dict):
            continue
        ident = str(user.get("id") or "")
        profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
        name = user.get("name") or profile.get("real_name") or ident
        if ident:
            names[ident] = str(name)
    return names


def slack_ts(value: str) -> str:
    stamp = datetime.fromtimestamp(float(value), UTC)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def reaction_count(raw: object) -> int:
    total = 0
    if not isinstance(raw, list):
        return 0
    for item in raw:
        if isinstance(item, dict):
            try:
                total += int(item.get("count") or 0)
            except (TypeError, ValueError):
                continue
    return total


def convert(root: Path) -> list[dict[str, Any]]:
    users = load_users(root)
    threads: dict[tuple[str, str], dict[str, Any]] = {}
    for channel_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        channel = channel_dir.name
        for day in sorted(channel_dir.glob("*.json")):
            payload = json.loads(day.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                continue
            for raw in payload:
                message = convert_message(raw, users)
                if message is None:
                    continue
                thread_id, encoded = message
                key = (channel, thread_id)
                if key not in threads:
                    threads[key] = {
                        "thread_id": thread_id,
                        "channel": channel,
                        "title": encoded["text"][:200] or thread_id,
                        "messages": [],
                    }
                threads[key]["messages"].append(encoded)
    return list(threads.values())


def convert_message(raw: object, users: dict[str, str]) -> tuple[str, dict[str, Any]] | None:
    if not isinstance(raw, dict) or raw.get("type") != "message" or raw.get("subtype"):
        return None
    text = raw.get("text")
    ts = raw.get("ts")
    if not isinstance(text, str) or not isinstance(ts, str):
        return None
    thread_id = str(raw.get("thread_ts") or ts)
    user = str(raw.get("user") or raw.get("username") or "unknown")
    encoded = {
        "id": str(raw.get("client_msg_id") or ts),
        "author": users.get(user, user),
        "ts": slack_ts(ts),
        "text": text,
        "reactions": reaction_count(raw.get("reactions")),
    }
    return thread_id, encoded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path, help="Slack export root (users.json + channels)")
    parser.add_argument("--out", type=Path, help="Write JSONL here; default stdout")
    args = parser.parse_args(argv)
    root = args.export_dir
    if not root.is_dir():
        parser.error("export_dir must be a directory")
    lines = [json.dumps(thread, ensure_ascii=False) for thread in convert(root)]
    text = "\n".join(lines) + ("\n" if lines else "")
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
