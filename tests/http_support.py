# SPDX-License-Identifier: Apache-2.0
"""Local OpenAI-compatible HTTP server for provider tests; no external network."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class Scripted:
    status: int = 200
    body: bytes = b""
    delay: float = 0.0
    headers: dict[str, str] = field(default_factory=dict)


def embed_body(vectors: list[list[float]], *, prompt: int = 3, model: str = "test") -> bytes:
    return json.dumps(
        {
            "object": "list",
            "model": model,
            "data": [
                {"object": "embedding", "index": index, "embedding": vector}
                for index, vector in enumerate(vectors)
            ],
            "usage": {"prompt_tokens": prompt, "total_tokens": prompt},
        }
    ).encode()


def chat_body(content: str, *, prompt: int = 3, completion: int = 5, model: str = "test") -> bytes:
    return json.dumps(
        {
            "id": "chatcmpl-test",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
        }
    ).encode()


class ScriptedServer(ThreadingHTTPServer):
    script: list[Scripted]
    requests: list[bytes]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        server = self.server
        assert isinstance(server, ScriptedServer)
        server.requests.append(body)
        spec = server.script.pop(0) if server.script else Scripted(status=500, body=b"empty")
        if spec.delay:
            time.sleep(spec.delay)
        self.send_response(spec.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(spec.body)))
        for key, value in spec.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(spec.body)


@contextmanager
def serve(script: list[Scripted]) -> Iterator[ScriptedServer]:
    server = ScriptedServer(("127.0.0.1", 0), Handler)
    server.script = list(script)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)
