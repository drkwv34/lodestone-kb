# Tasks

## 1. Embedders

- [ ] 1.1 Add `lodestone.vectors` (`embedder`, `hash`, `openai_compat`) with `Embedder.embed(list[str]) -> list[list[float]]`, extend import-linter, and verify `test_fr_061_hash_embedder_deterministic` plus a local httpx embedder retry/`llm_log` test.

## 2. Backends and storage writes

- [ ] 2.1 Implement `BruteForceBackend` and `SqliteVecBackend` (lazy per model/dim; sqlite-vec skip when absent) and verify `test_fr_033_backend_parity_1000_vectors`.
- [ ] 2.2 Write card/chunk/burst embeddings in the ingest derived-data transaction, delete them with records, and verify `test_fr_033_embeddings_deleted_with_records_and_replaced_on_thread_change` plus mismatch handling.

## 3. Lanes, offline and reindex

- [ ] 3.1 Add `vec_card`/`vec_chunk` with `result.notices` when disabled or mismatched and verify `test_fr_033_vec_lanes_skipped_with_notice_when_disabled`.
- [ ] 3.2 Add `--offline` / `offline=true` hash swap, `OfflineError` on remote attempts, and verify `test_fr_062_offline_guard_hash_embedder_and_remote_raises`.
- [ ] 3.3 Add `reindex --lanes vec` from stored text only and verify `test_fr_083_reindex_lanes_vec_row_counts_identical`.

## 4. Integration checks

- [ ] 4.1 Run `openspec validate add-vector-lanes --strict`, ruff, mypy --strict, import-linter, module-size gate, and pytest with coverage >= 80%.

## Workflow follow-up

- Archive the change on main after merge as a direct commit.
- Do not archive from the feature branch.
