# Design

## Context

See proposal.md. Bench already consumes a files+threads corpus plus
`evalset.v1`. MCP already runs as `lodestone mcp` over stdio. Packaging is
`0.1.0.dev0` with a tag-triggered draft GitHub Release and no PyPI job.
Default tests remain offline.

## Goals / Non-Goals

**Goals:**
- Map BEIR corpus/queries/qrels onto the existing files connector and
  evalset schema without new storage tables.
- Build the MCP image in CI on Ubuntu only.
- Single source of version `0.1.0rc1` shared by package metadata and
  `lodestone --version`.

**Non-Goals:**
- Publishing to PyPI, tagging `v0.1.0`, or creating a GitHub Release.
- Downloading SciFact in default tests or CI.
- Rewriting retrieval, storage, or shipped strategies.
- Starting other Could items besides FR-079.

## Decisions

1. **Local `--from` is the default test path.** `bench import beir:scifact`
   reads a directory (or zip) with `corpus.jsonl`, `queries.jsonl`, and
   `qrels/*.tsv`. Documents become `docs/<id>.md`; gold ids are those
   relative paths so they match files-connector `ext_id`. Category is
   `paraphrase` when gold ids exist, `unanswerable` when they do not.
   Alternative: add a `beir` evalset category; rejected because that
   would break the frozen `evalset.v1` enum.

2. **Published SciFact checksum is MD5.** BEIR documents
   `5f7d1de60b170fc8027bb7898e2efca1` for `scifact.zip`. Download (when
   `--from` is omitted) verifies that MD5 before extract. Inventing a
   SHA-256 would not match the published digest. Local fixtures are not
   the public zip, so they skip the mirror MD5 and are used via `--from`.

3. **Download uses httpx and is network-marked.** A unit test feeds a
   fake fetch returning a zip whose MD5 is wrong or right. The live
   mirror test is `@pytest.mark.network` and stays deselected.

4. **Dockerfile stays slim and stdio.** `python:3.12-slim`, install the
   package, `ENTRYPOINT ["lodestone", "mcp"]`, `CMD ["--offline"]`.
   `.dockerignore` drops tests, git, docs, and OpenSpec. CI job `docker`
   runs on `ubuntu-latest` only with a block-scalar `docker build`. No
   push, no login. Alternative: multi-arch or GHCR publish; rejected for
   the candidate.

5. **Version is PEP 440 `0.1.0rc1`.** Hatch reads `__version__` from
   `src/lodestone/__init__.py`. Git tag is `v0.1.0-rc1` (semver tag
   form). CLI `--version` prints the PEP 440 string. Fallback in the
   bench runner uses the same constant.

6. **H1–H5 stay not tested unless committed numbers suffice.** The
   recorded synth run used the hash embedder and omitted
   `lodestone-hybrid`, decay pairing, and `full-context`. Do not infer
   hold/not-hold from inapplicable hash-embedder scores.

7. **FR-079 is in scope despite the SRS “C after tag” line.** The
   delivery-plan release-candidate slot lists FR-079 first. Record that
   in `docs/decisions/0008-release-candidate.md`. Other Could work stays
   deferred.

## Risks / Trade-offs

- [Public SciFact zip MD5 changes] → pin the published digest; mismatch
  fails closed; `--from` still works.
- [BEIR ids unsafe as filenames] → sanitise to `[A-Za-z0-9._-]` and keep
  the mapping in gold ids via the written relative path.
- [Docker unavailable on macOS/Windows runners] → Ubuntu-only job.
- [Quoted YAML `run: "$VAR"` schedules zero jobs] → block scalars only.
- [Hash-embedder scores mistaken for H1–H5 results] → table says not
  tested and restates the hash caveat.

## Migration Plan

No schema migration. Existing workspaces are unchanged. Rollback is
reverting the feature branch. Tag `v0.1.0-rc1` only after main CI is
green on the archive commit.

## Open Questions

None.
