# Spec Delta

## Purpose

Import BEIR-format retrieval corpora (SciFact) into a Lodestone bench
corpus and evalset.v1 so strategy comparisons can run on published IR
datasets without requiring a download in the default test suite.

## ADDED Requirements

### Requirement: FR-079 offline BEIR import
The CLI SHALL accept `lodestone bench import beir:scifact` with `--from`
pointing at a local BEIR-format directory or zip (corpus.jsonl,
queries.jsonl, qrels TSV) and `--out` for the converted corpus. The
command SHALL write markdown documents under `docs/` and an `evalset.v1`
JSONL whose `gold_ids` are files-connector `ext_id` values. Default tests
MUST NOT download.

#### Scenario: Tiny local fixture converts without network
- **WHEN** `lodestone bench import beir:scifact --from` a tiny BEIR-format
  fixture `--out` a destination directory
- **THEN** the destination contains `docs/*.md` and a valid `evalset.v1`
  whose gold ids match document `ext_id` values, and no network call is
  made

### Requirement: FR-079 checksummed optional download
When `--from` is omitted, `bench import beir:scifact` SHALL download the
public BEIR SciFact zip and verify the published MD5
`5f7d1de60b170fc8027bb7898e2efca1` before extracting. A checksum mismatch
SHALL abort without writing a corpus. This path SHALL be skipped in the
default test run unless `LODESTONE_NETWORK_TESTS=1`.

#### Scenario: Checksum mismatch rejects the archive
- **WHEN** a download or zip is supplied whose digest does not match the
  pinned SciFact checksum
- **THEN** import fails with a checksum error and does not write evalset
  files

#### Scenario: Network import is opt-in
- **WHEN** the default pytest run executes
- **THEN** no test downloads SciFact; the download path is marked
  `network` and stays deselected
