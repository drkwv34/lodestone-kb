# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_nfr_017_license_and_notice() -> None:
    license_text = (ROOT / "LICENSE").read_text()
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text
    assert "Christian Agila" in (ROOT / "NOTICE").read_text()


def test_nfr_012_module_limit_and_spdx_headers() -> None:
    for directory in ("src", "tests", "scripts"):
        for path in (ROOT / directory).rglob("*.py"):
            lines = path.read_text().splitlines()
            assert len(lines) <= 500, path
            assert lines[0] == "# SPDX-License-Identifier: Apache-2.0", path
