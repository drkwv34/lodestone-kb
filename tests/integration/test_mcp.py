# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
import socket
import sqlite3
from pathlib import Path

import pytest

from lodestone.config import load_config
from lodestone.fusion.packet import validate_packet
from lodestone.mcp_server import create_server, readonly_connection
from tests.helpers import synced_workspace

TOOLS = ["get_record", "grep", "list_sources", "recent", "search", "who_knows"]


def _payload(result: object) -> dict[str, object]:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(result, "content", None) or []
    for item in content:
        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            loaded = json.loads(text)
            if isinstance(loaded, dict):
                return loaded
    raise AssertionError(f"no JSON payload in {result!r}")


async def _call(config_path: Path, name: str, arguments: dict[str, object]) -> dict[str, object]:
    from mcp.client import Client

    server = create_server(load_config(config_path), offline=True)
    async with Client(server) as client:
        listed = await client.list_tools()
        assert sorted(tool.name for tool in listed.tools) == TOOLS
        result = await client.call_tool(name, arguments)
        assert not getattr(result, "is_error", False), result
        return _payload(result)


def test_fr_052_mcp_tools_validate_against_schema(tmp_path: Path) -> None:
    config_path = synced_workspace(tmp_path)

    async def scenario() -> None:
        from mcp.client import Client

        server = create_server(load_config(config_path), offline=True)
        async with Client(server) as client:
            listed = await client.list_tools()
            names = sorted(tool.name for tool in listed.tools)
            assert names == TOOLS
            for tool in listed.tools:
                assert isinstance(tool.input_schema, dict)
                assert tool.input_schema.get("type") == "object"
            searched = _payload(await client.call_tool("search", {"query": "ERR_MANIFEST_TIMEOUT"}))
            hits = searched["hits"]
            assert isinstance(hits, list) and hits
            for hit in hits:
                assert isinstance(hit, dict)
                validate_packet(hit)
            grepped = _payload(await client.call_tool("grep", {"pattern": "ERR_MANIFEST_TIMEOUT"}))
            assert grepped["matches"]
            record = _payload(await client.call_tool("get_record", {"ext_id": "manifest.md"}))
            assert "raw_text" in record and "children" in record and "record" in record
            ident = record["record"]["id"]
            by_id = _payload(
                await client.call_tool("get_record", {"id": ident, "include_card": False})
            )
            assert by_id["card"] is None
            listed_sources = _payload(
                await client.call_tool("list_sources", {"project": "default"})
            )
            assert listed_sources["projects"]
            sources = _payload(await client.call_tool("list_sources", {}))
            assert sources["sources"]
            people = _payload(await client.call_tool("who_knows", {"topic": "manifest"}))
            assert "people" in people
            recent = _payload(await client.call_tool("recent", {"limit": 3}))
            assert recent["hits"]
            for hit in recent["hits"]:
                assert isinstance(hit, dict)
                validate_packet(hit)

    asyncio.run(scenario())


def test_fr_043_mcp_who_knows_returns_people(tmp_path: Path) -> None:
    config_path = synced_workspace(tmp_path)
    payload = asyncio.run(_call(config_path, "who_knows", {"topic": "manifest", "limit": 5}))
    people = payload["people"]
    assert isinstance(people, list)
    if people:
        assert {"author", "score", "records"} <= set(people[0])


def test_fr_044_mcp_recent_returns_evidence(tmp_path: Path) -> None:
    config_path = synced_workspace(tmp_path)
    payload = asyncio.run(_call(config_path, "recent", {"limit": 5}))
    hits = payload["hits"]
    assert hits
    for hit in hits:
        assert isinstance(hit, dict)
        validate_packet(hit)


def test_fr_052_offline_mcp_makes_no_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = synced_workspace(tmp_path)
    real = socket.socket

    def blocked(*args: object, **kwargs: object) -> socket.socket:
        family = args[0] if args else kwargs.get("family", socket.AF_INET)
        if family in (socket.AF_INET, socket.AF_INET6):
            raise OSError("network disabled")
        return real(*args, **kwargs)  # type: ignore[misc]

    monkeypatch.setattr(socket, "socket", blocked)
    payload = asyncio.run(_call(config_path, "search", {"query": "ERR_MANIFEST_TIMEOUT"}))
    assert payload["hits"]


def test_fr_052_readonly_db_rejects_writes(tmp_path: Path) -> None:
    config_path = synced_workspace(tmp_path)
    config = load_config(config_path)
    connection = readonly_connection(config.workspace.db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute(
                "INSERT INTO sources(name,kind,config_json) VALUES('x','files','{}')"
            )
            connection.commit()
    finally:
        connection.close()
