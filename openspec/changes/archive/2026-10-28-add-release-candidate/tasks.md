# Tasks

## 1. BEIR adapter (FR-079)

- [x] 1.1 Add `lodestone.bench.beir` to convert a local BEIR directory or zip
      into `docs/*.md` plus `evalset.v1`, and verify
      `test_fr_079_offline_fixture_imports_without_network`.
- [x] 1.2 Add `lodestone bench import beir:scifact` with `--from` and `--out`,
      pin SciFact MD5 `5f7d1de60b170fc8027bb7898e2efca1` for downloads, and
      verify `test_fr_079_checksum_mismatch_rejects` plus import `--help`.
- [x] 1.3 Mark live-mirror download `@pytest.mark.network`, keep it deselected
      in the default run, and verify `test_fr_079_network_download_is_opt_in`.

## 2. MCP container and CI

- [x] 2.1 Add `Dockerfile` and `.dockerignore` with entrypoint `lodestone mcp`
      and default `--offline`, and verify `test_fr_mcp_dockerfile_entrypoint`.
- [x] 2.2 Add an Ubuntu-only `docker` CI job that runs `docker build` with a
      block scalar, no push, and verify the workflow YAML contains `docker build`
      and no `docker push`.

## 3. Version, changelog, findings, and gates

- [x] 3.1 Set package version `0.1.0rc1` from `__version__`, add CLI
      `--version`, and verify `test_fr_version_cli_matches_package`.
- [x] 3.2 Write Keep a Changelog `0.1.0rc1` and `docs/RELEASE.md` (no PyPI
      publish), and verify those files exist with the required wording.
- [x] 3.3 Update FINDINGS H1–H5 (held / not held / not tested) from committed
      numbers only, keep `status: not run - needs keys`, and verify
      `test_nfr_benchmark_findings_not_run_needs_keys`.
- [x] 3.4 Record deferred Could work and the FR-079 exception in
      `docs/decisions/0008-release-candidate.md`, add the requirements status
      table to evidence, and verify the decision file exists.
- [x] 3.5 Run `openspec validate add-release-candidate --strict`, mypy
      `--strict`, ruff, import-linter, module-size, link check, and pytest
      with coverage at least 85%.

## Workflow follow-up

- Open a ready PR from `feat/release-candidate`.
- After green PR CI including macOS, merge locally with `git merge --no-ff`.
- Archive `add-release-candidate` as a direct main commit after merge.
- After green main CI including macOS, tag `v0.1.0-rc1` and push the tag.
- Do not archive from the feature branch. Do not publish to PyPI.
