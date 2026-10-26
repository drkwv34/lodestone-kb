# SPDX-License-Identifier: Apache-2.0
"""Load builtin and entry-point connectors (group lodestone.connectors)."""

from __future__ import annotations

from collections.abc import Iterator
from importlib.metadata import entry_points
from typing import Any, Protocol, cast

from lodestone.config import Source
from lodestone.connectors.files import FilesConnector, RawItem, Skip
from lodestone.connectors.threads import ThreadsConnector

BUILTIN = {"files": FilesConnector, "threads": ThreadsConnector}


class Connector(Protocol):
    """Discover RawItems for one configured source."""

    skipped: list[Skip]

    def discover(self, cfg: Source) -> Iterator[RawItem]: ...


def entrypoint_connectors() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for item in entry_points(group="lodestone.connectors"):
        loaded[item.name] = item.load()
    return loaded


def _instantiate(cls: Any) -> Connector:
    connector = cls()
    if not hasattr(connector, "skipped"):
        connector.skipped = []
    if not callable(getattr(connector, "discover", None)):
        raise TypeError("connector must implement discover()")
    return cast(Connector, connector)


def connector_for(source: Source) -> Connector:
    if source.kind in BUILTIN:
        return _instantiate(BUILTIN[source.kind])
    plugins = entrypoint_connectors()
    try:
        cls = plugins[source.kind]
    except KeyError as exc:
        raise ValueError(f"unsupported source kind: {source.kind}") from exc
    return _instantiate(cls)
