# SPDX-License-Identifier: Apache-2.0
"""Doctor probes for runtime, schema, providers, and optional deep checks."""

from __future__ import annotations

import platform
import sqlite3
from dataclasses import dataclass, field

import httpx

from lodestone.config import Config
from lodestone.storage.consistency import deep_errors
from lodestone.storage.db import (
    SCHEMA_VERSION,
    StorageError,
    inspect_database,
    open_database,
    probe_fts5,
)

try:
    import sqlite_vec  # type: ignore[import-untyped]
except ImportError:
    sqlite_vec = None


@dataclass
class DoctorReport:
    lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _probe_provider(config: Config, *, offline: bool) -> str | None:
    if offline or config.offline or config.llm is None:
        return None
    url = str(config.llm.base_url)
    try:
        response = httpx.get(url, timeout=2.0)
        return f"Provider: reachable (HTTP {response.status_code})"
    except httpx.HTTPError as extra:
        return f"provider unreachable: {extra}"


def run_doctor(config: Config, *, deep: bool = False, offline: bool = False) -> DoctorReport:
    report = DoctorReport()
    report.lines.append(f"Python: {platform.python_version()}")
    report.lines.append(f"SQLite: {sqlite3.sqlite_version}")
    if sqlite3.sqlite_version_info < (3, 38, 0):
        report.errors.append("SQLite >= 3.38 required")
    try:
        probe_fts5()
        report.lines.append("FTS5: available (identifier tokenizer probe passed)")
    except StorageError as extra:
        report.errors.append(str(extra))
    if sqlite_vec is not None:
        report.lines.append("sqlite-vec: available")
    else:
        report.lines.append("sqlite-vec: not installed")
    try:
        version = inspect_database(config.workspace.db_path)
        report.lines.append(f"Database schema: {version} (supported: {SCHEMA_VERSION})")
        if version != SCHEMA_VERSION:
            report.errors.append("Database requires migration; run lodestone init")
    except (sqlite3.Error, StorageError) as extra:
        report.errors.append(f"Database: {extra}; run lodestone init or upgrade Lodestone")
    probed = _probe_provider(config, offline=offline)
    if probed is None:
        report.lines.append("Provider: skipped (offline or unconfigured)")
    elif probed.startswith("Provider:"):
        report.lines.append(probed)
    else:
        report.errors.append(probed)
    if deep and not report.errors:
        connection = open_database(config.workspace.db_path)
        try:
            report.errors.extend(deep_errors(connection))
        finally:
            connection.close()
        if not report.errors:
            report.lines.append("Deep: FTS, term_stats, embeddings, and orphans OK")
    if not report.errors:
        suffix = " (deep checks passed)" if deep else ""
        report.lines.append(f"Doctor: OK{suffix}")
    return report
