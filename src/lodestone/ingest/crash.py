# SPDX-License-Identifier: Apache-2.0
"""Optional SIGKILL hook used by the crash-injection harness."""

from __future__ import annotations

import os
import signal


def maybe_crash() -> None:
    """Kill this process after N parent commits when LODESTONE_CRASH_AFTER is set."""
    raw = os.environ.get("LODESTONE_CRASH_AFTER")
    if raw is None or raw == "":
        return
    left = int(raw)
    if left <= 0:
        os.kill(os.getpid(), getattr(signal, "SIGKILL", signal.SIGTERM))
    os.environ["LODESTONE_CRASH_AFTER"] = str(left - 1)
