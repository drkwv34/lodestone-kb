# Design

## Context

See proposal.md. README still treats MCP and bench as planned. `docs/mcp.md`,
`docs/privacy.md`, and `docs/providers.md` exist. CI already lints modules,
builds a wheel, and reinstalls it in-place with `--no-deps`. FR-064 snippets
live in `docs/providers.md`. FR-078 resume cache already has
`test_fr_078_resume_zero_duplicate_llm_calls`. Tests must stay offline.

## Goals / Non-Goals

**Goals:**
- Make README and user guides match shipped CLI/SDK/MCP/bench behaviour.
- Run quickstart and internal link checks in default CI.
- Install the built wheel in a clean venv (with its dependencies) in the
  existing `build` job.
- Record one synthetic offline bench run with real output; mark real-embedder
  work as not run.

**Non-Goals:**
- Publishing to PyPI, tagging `v0.1.0`, or rewriting retrieval/storage.
- Reimplementing FR-078.
- Hitting live provider APIs or inventing FINDINGS numbers.
- Checking external HTTP URLs in the default (no-network) test run.

## Decisions

1. **README follows the bootstrap skeleton but stays truthful.** Quickstart
   shows `pip install lodestone-kb` as the intended distribution and a
   from-source fallback, because this tree is `0.1.0.dev0` and is not
   published to PyPI. Comparison table lists shipped capabilities, not
   roadmap placeholders. Alternative: copy the skeleton commands verbatim
   including `pip install lodestone-kb` as the only path; rejected because
   it would fail today.

2. **Quickstart script is self-contained and offline.** It creates a temp
   workspace, writes a tiny `docs/` file containing `ERR_MANIFEST_TIMEOUT`,
   then `init` / `source add` / `sync --offline` / `search --explain`. CI
   invokes the script after the editable install so `lodestone` is on PATH.
   Pytest wraps the same script. Alternative: clone the repo into the temp
   dir; rejected because that is slower and needs the checkout layout.

3. **Link checker is a local Python script.** `scripts/check_links.py` parses
   markdown links and images in README and `docs/{quickstart,concepts,
   connectors,mcp,bench,privacy,faq}.md` (and pages they link to under
   `docs/`). Relative targets must exist. `http://` and `https://` URLs are
   skipped unless `LODESTONE_CHECK_EXTERNAL=1`. Alternative: lychee; rejected
   to avoid a new CI binary and network in default tests.

4. **Clean-venv wheel install lives in the `build` job.** Replace
   `--force-reinstall --no-deps` with `python -m venv`, `pip install
   dist/*.whl`, then run `scripts/smoke_wheel.py` using that venv's
   `lodestone`. The job has network for dependency resolution. Pytest keeps
   a PATH-based smoke against the test env (no extra download). Alternative:
   pytest-only clean venv; rejected because default tests forbid network.

5. **FR-064 stays in `docs/providers.md`.** FAQ and README link there. The
   existing config-schema test remains the acceptance test; extend it only if
   additional ` ```toml ` preset blocks appear.

6. **Synthetic bench uses a small, actually executed corpus.** Run
   `lodestone bench synth` with a modest `--threads` (not 300) plus offline
   strategies that finish locally, paste the real `report.md` excerpt and
   command, and caveat the hash embedder. Hypotheses H1–H5 that need a real
   embedder stay untested. Alternative: claim the 300-thread protocol; rejected
   if that run is not performed.

7. **Release workflow is tag-only and never publishes to PyPI.**
   `.github/workflows/release.yml` builds wheel+sdist on `v*` tags, uploads
   artifacts, and opens a draft GitHub Release.

8. **Semver policy is documentation plus the existing 500-line lint.** Public
   surfaces: `lodestone` SDK, MCP tool schemas, and `*.v1` JSON schemas.
   Breaking changes bump major (or the schema suffix). Deprecations warn for
   one minor. No runtime deprecation helper is added until something is
   actually deprecated.

## Risks / Trade-offs

- [README `pip install lodestone-kb` fails until a release is published] →
  document the from-source install immediately below.
- [Clean-venv job fails if PyPI is unreachable] → keep it in the networked
  `build` job, not in default pytest.
- [Link checker false-positives on anchors or badges] → ignore fragment-only
  links; skip `https://` badge URLs.
- [Quickstart temp dirs on Windows] → script uses `mktemp` on POSIX; Windows
  CI remains the smoke subset and does not run the shell script.

## Migration Plan

Docs-only plus CI job changes. Existing workspaces are unaffected. Rollback is
reverting the feature branch. No schema migration.

## Open Questions

None. Real-embedder runs stay `not run - needs keys` unless keys appear in
the environment at apply time.
