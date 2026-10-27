# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_DOCS = (
    "README.md",
    "docs/quickstart.md",
    "docs/concepts.md",
    "docs/connectors.md",
    "docs/mcp.md",
    "docs/bench.md",
    "docs/privacy.md",
    "docs/faq.md",
    "docs/providers.md",
    "docs/compatibility.md",
    "docs/benchmarks/FINDINGS.md",
)


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(  # noqa: S603
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=merged,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="examples/quickstart.sh is POSIX")
def test_nfr_013_quickstart_script_offline() -> None:
    script = ROOT / "examples/quickstart.sh"
    assert script.is_file()
    result = _run(["bash", str(script)])
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "ERR_MANIFEST_TIMEOUT" in output


def test_nfr_016_readme_and_docs_internal_links() -> None:
    for relative in REQUIRED_DOCS:
        assert (ROOT / relative).is_file(), relative
    result = _run([sys.executable, str(ROOT / "scripts/check_links.py")])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Link check:" in result.stdout


def test_nfr_014_module_size_and_semver_policy() -> None:
    policy = (ROOT / "docs/compatibility.md").read_text(encoding="utf-8")
    assert "semver" in policy.lower() or "semantic versioning" in policy.lower()
    assert "one minor" in policy.lower()
    result = _run([sys.executable, str(ROOT / "scripts/check_modules.py")])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "<= 500 lines" in result.stdout


def test_wheel_smoke_cli() -> None:
    result = _run([sys.executable, str(ROOT / "scripts/smoke_wheel.py")])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Wheel smoke:" in result.stdout


def test_nfr_benchmark_findings_not_run_needs_keys() -> None:
    text = (ROOT / "docs/benchmarks/FINDINGS.md").read_text(encoding="utf-8")
    assert "status: not run - needs keys" in text
    assert "hash embedder is not semantic" in text.lower() or "not semantic" in text.lower()


def test_release_workflow_has_no_pypi_publish() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "pypi" not in text.lower()
    assert "draft: true" in text
    assert "python -m build" in text
