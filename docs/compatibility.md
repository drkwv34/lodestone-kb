# Compatibility policy (NFR-014)

Public surfaces follow semantic versioning after the first `0.1.0` release:

- Python SDK (`lodestone.Lodestone` and exported types)
- MCP tool names and JSON argument schemas
- On-disk JSON schemas (`evidence.v1`, `evalset.v1`, `report.v1`)

Breaking changes bump the major version, or the schema suffix for JSON
schemas (`v1` → `v2`). Additive fields may appear in a minor release.

Deprecations warn for **one minor version** before the symbol, flag, or
schema field is removed. This tree is `0.1.0rc1`; nothing is deprecated
yet, so there is no runtime warning helper. See [RELEASE.md](RELEASE.md).

Each Python module under `src/`, `tests/`, and `scripts/` stays at or below
500 lines. CI runs `python scripts/check_modules.py` on every pull request.
