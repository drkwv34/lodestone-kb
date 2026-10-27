# Tasks

## 1. User guides, quickstart, and FR-064

- [x] 1.1 Rewrite README from the bootstrap skeleton, accurate to shipped
      commands, and verify internal links in the README resolve.
- [x] 1.2 Add `docs/quickstart.md`, `docs/concepts.md`, `docs/connectors.md`,
      `docs/bench.md`, and `docs/faq.md`; extend `docs/mcp.md` and
      `docs/privacy.md` as needed; verify those pages exist.
- [x] 1.3 Add `examples/quickstart.sh` (offline init, source add, sync,
      search `ERR_MANIFEST_TIMEOUT`) and verify
      `test_nfr_013_quickstart_script_offline`.
- [x] 1.4 Keep Cerebras, OpenAI, and Ollama TOML presets in
      `docs/providers.md` and verify
      `test_fr_064_provider_preset_snippets_validate`.

## 2. Link check, semver policy, wheel, and benchmarks

- [x] 2.1 Add `scripts/check_links.py` plus a CI step, skip external URLs,
      and verify `test_nfr_016_readme_and_docs_internal_links`.
- [x] 2.2 Document public-API semver and one-minor deprecation warnings, keep
      the 500-line module lint, and verify
      `test_nfr_014_module_size_and_semver_policy`.
- [x] 2.3 Build wheel + sdist, install `dist/*.whl` into a clean venv in the
      `build` job, run `scripts/smoke_wheel.py` from that venv, and verify
      `test_wheel_smoke_cli` against the test environment.
- [x] 2.4 Run a synthetic offline bench, paste real numbers into
      `docs/benchmarks/`, write `FINDINGS.md` with
      `status: not run - needs keys` for the real-embedder run, and verify
      `test_nfr_benchmark_findings_not_run_needs_keys`.
- [x] 2.5 Cite existing `test_fr_078_resume_zero_duplicate_llm_calls`; do not
      reimplement resume cache. Verify the test still passes.

## 3. Release workflow, contributing, and gates

- [x] 3.1 Add `.github/workflows/release.yml` for `v*` tags (wheel+sdist,
      artifacts, draft GitHub release, no PyPI publish) and a CHANGELOG for
      `0.1.0.dev0`; verify the workflow YAML contains no PyPI publish step.
- [x] 3.2 Update CONTRIBUTING.md with connector docs, compatibility policy,
      and packaging notes; verify links to `docs/connectors.md`.
- [x] 3.3 Run `openspec validate add-docs-packaging --strict`, mypy --strict,
      ruff, import-linter, module-size, and pytest with coverage at least 85%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
- Paste real command output in `docs/evidence/docs-packaging.md`.
