# SPDX-License-Identifier: Apache-2.0
"""Stable content hashes for incremental ingest."""

from __future__ import annotations

import hashlib
import unicodedata

from lodestone.chunking import code, markdown

CHUNKER_VERSION = markdown.VERSION + "/" + code.VERSION
THREAD_VERSION = "thread-v1"


def content_hash(text: str, version: str = CHUNKER_VERSION) -> str:
    normalised = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return hashlib.sha256((version + "\x00" + normalised).encode("utf-8")).hexdigest()
