# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lodestone.cli import app

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner(env={"NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"})
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
    "docs/RELEASE.md",
    "CHANGELOG.md",
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
    lowered = text.lower()
    for hypothesis in ("h1", "h2", "h3", "h4", "h5"):
        assert hypothesis in lowered
    assert "not tested" in lowered
    assert "held / not held / not tested" in lowered or "| not tested |" in lowered


def test_fr_version_cli_matches_package() -> None:
    from importlib.metadata import version

    from lodestone import __version__

    result = runner.invoke(app, ["--version"], color=False)
    assert result.exit_code == 0, result.output
    assert __version__ == "0.1.0rc1"
    assert version("lodestone-kb") == "0.1.0rc1"
    assert "0.1.0rc1" in result.output


def test_fr_mcp_dockerfile_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "ENTRYPOINT" in dockerfile
    assert "lodestone" in dockerfile
    assert "mcp" in dockerfile
    assert "--offline" in dockerfile
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "tests" in dockerignore
    assert ".git" in dockerignore
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "docker build" in workflow
    assert "docker push" not in workflow
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.0rc1]" in changelog
    release = (ROOT / "docs/RELEASE.md").read_text(encoding="utf-8")
    assert "v0.1.0-rc1" in release
    assert "PyPI" in release
    assert (ROOT / "docs/decisions/0008-release-candidate.md").is_file()


def test_release_workflow_has_no_pypi_publish() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "pypi" not in text.lower()
    assert "draft: true" in text
    assert "python -m build" in text
