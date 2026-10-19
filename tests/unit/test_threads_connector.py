# SPDX-License-Identifier: Apache-2.0
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest

from lodestone.config import Source
from lodestone.connectors.files import RawItem
from lodestone.connectors.threads import ThreadsConnector, parse_ts, render_transcript

TS = datetime(2026, 7, 1, 9, 14, tzinfo=UTC)


def valid_thread(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "thread_id": "thread_8f42",
        "channel": "ckpt-support",
        "title": "Restore stalls after manifest load",
        "messages": [
            {
                "id": "m1",
                "author": "maya",
                "ts": "2026-07-01T09:14:00Z",
                "text": "Is NFS stalled?",
            },
            {
                "id": "m2",
                "author": "owen",
                "ts": "2026-07-01T09:21:00+00:00",
                "text": "Set CKPT_PREFETCH=4 on the mount.",
                "reactions": 2,
            },
        ],
    }
    payload.update(overrides)
    return payload


def write_jsonl(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def discover(path: Path) -> tuple[ThreadsConnector, list[RawItem]]:
    connector = ThreadsConnector()
    items = list(connector.discover(Source(name="support", kind="threads", path=path)))
    return connector, items


def test_fr_011_malformed_jsonl_reports_line_numbers(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = write_jsonl(
        tmp_path / "threads.jsonl",
        [
            json.dumps(valid_thread()),
            "{not json",
            json.dumps({"thread_id": "x"}),
            "",
            json.dumps(valid_thread(thread_id="kept")),
        ],
    )
    with caplog.at_level(logging.WARNING):
        connector, items = discover(path)
    assert [item.ext_id for item in items] == ["thread_8f42", "kept"]
    skipped = {item.path: item.reason for item in connector.skipped}
    assert "line 2" in skipped
    assert "line 3" in skipped
    assert "line 4" not in skipped
    assert "line 2" in caplog.text and "line 3" in caplog.text
    assert items[0].kind_hint == "thread"
    assert "maya" in items[0].text and "CKPT_PREFETCH" in items[0].text
    assert json.loads(items[0].metadata["messages_json"])[0]["id"] == "m1"


def test_fr_011_timezone_offsets_z_and_naive_rejected(tmp_path: Path) -> None:
    assert parse_ts("2026-07-01T09:14:00Z") == TS
    assert parse_ts("2026-07-01T09:14:00+00:00") == TS
    assert parse_ts("2026-07-01T04:14:00-05:00") == TS
    with pytest.raises(ValueError, match="naive"):
        parse_ts("2026-07-01T09:14:00")
    with pytest.raises(ValueError, match="ISO-8601"):
        parse_ts("not-a-date")
    path = write_jsonl(
        tmp_path / "tz.jsonl",
        [
            json.dumps(valid_thread()),
            json.dumps(
                valid_thread(
                    thread_id="naive",
                    messages=[
                        {
                            "id": "n1",
                            "author": "maya",
                            "ts": "2026-07-01T09:14:00",
                            "text": "naive",
                        }
                    ],
                )
            ),
        ],
    )
    connector, items = discover(path)
    assert [item.ext_id for item in items] == ["thread_8f42"]
    assert connector.skipped[0].path == "line 2"
    assert "naive" in connector.skipped[0].reason
    rendered = render_transcript(items[0].messages or ())
    assert rendered.startswith("[2026-07-01T09:14Z] maya:")
    with pytest.raises(ValueError, match="ISO-8601"):
        parse_ts("")
    with pytest.raises(ValueError, match="ISO-8601"):
        parse_ts(None)


def test_fr_011_default_title_and_source_channel(tmp_path: Path) -> None:
    payload = valid_thread()
    del payload["title"]
    del payload["channel"]
    path = write_jsonl(tmp_path / "t.jsonl", [json.dumps(payload)])
    items = list(
        ThreadsConnector().discover(
            Source(name="support", kind="threads", path=path, channel="ops")
        )
    )
    assert items[0].title.startswith("Is NFS")
    assert items[0].metadata["channel"] == "ops"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ([], "JSON object"),
        (
            {"messages": [{"id": "1", "author": "a", "ts": "2026-07-01T09:14:00Z", "text": "x"}]},
            "thread_id",
        ),
        (
            valid_thread(
                messages=[{"id": "1", "author": "a", "ts": "2026-07-01T09:14:00Z", "text": 1}]
            ),
            "text must be a string",
        ),
        (
            valid_thread(messages=["not-an-object"]),
            "must be an object",
        ),
        (
            valid_thread(
                messages=[{"id": "", "author": "a", "ts": "2026-07-01T09:14:00Z", "text": "x"}]
            ),
            "missing id",
        ),
        (
            valid_thread(
                messages=[{"id": "1", "author": "", "ts": "2026-07-01T09:14:00Z", "text": "x"}]
            ),
            "missing author",
        ),
        (
            valid_thread(
                messages=[
                    {
                        "id": "1",
                        "author": "a",
                        "ts": "2026-07-01T09:14:00Z",
                        "text": "x",
                        "reactions": -1,
                    }
                ]
            ),
            "reactions",
        ),
        (valid_thread(channel=1), "channel must be a string"),
        (valid_thread(title=1), "title must be a string"),
    ],
)
def test_fr_011_invalid_thread_objects_skipped(
    tmp_path: Path, payload: object, reason: str
) -> None:
    path = write_jsonl(tmp_path / "bad.jsonl", [json.dumps(payload)])
    connector, items = discover(path)
    assert items == []
    assert reason in connector.skipped[0].reason


def test_fr_011_threads_path_must_be_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be a file"):
        list(ThreadsConnector().discover(Source(name="x", kind="threads", path=tmp_path)))


def test_fr_011_oversize_and_invalid_utf8_lines_skipped(tmp_path: Path) -> None:
    path = tmp_path / "mixed.jsonl"
    with path.open("wb") as stream:
        stream.write((json.dumps(valid_thread()) + "\n").encode())
        stream.write(b"\xff\xfe\n")
        stream.write((json.dumps(valid_thread(thread_id="huge")) + "\n").encode())
    connector, items = discover(path)
    source = Source(name="support", kind="threads", path=path, max_file_bytes=8)
    tiny = ThreadsConnector()
    skipped = list(tiny.discover(source))
    assert skipped == []
    assert tiny.skipped
    assert any("invalid UTF-8" in item.reason for item in connector.skipped)
    assert items[0].ext_id == "thread_8f42"
