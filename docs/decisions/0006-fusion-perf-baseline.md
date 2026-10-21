# Fusion search performance baseline

Measured on Linux 6.12.94+ x86_64, Python 3.12.3, `pytest -m perf`.

| ID | Target | Measured | Status |
|---|---|---|---|
| NFR-001 lexical fused search p95 at 20,000 records | <= 50 ms laptop / 150 ms GitHub runner | 2.692 ms | Met |
| NFR-002 heuristic-card ingest throughput excluding embeddings | >= 200 records/s | 81.333 records/s (20,000 files in 245.904 s) | Below target |
| NFR-003 incremental no-change sync of 20,000 records | <= 10 s | 2.984 s | Met |

## Plan for NFR-002

Heuristic cards run in a per-parent transaction with IDF lookups and optional section children even for heading-less text files. This first measurement is on a shared cloud VM, not a 2024-class laptop, and still writes 20,000 heuristic cards.

Follow-up work, without weakening the gate:

1. Skip empty heading-less child chunks so a plain `.txt` file stays one record.
2. Batch `term_stats` reads used by heuristic entity scoring.
3. Re-measure on a 2024-class laptop; keep printing the CI number beside it.
4. If still below 200 records/s, consider a dedicated ingest worker for derived cards after the lexical upsert, still in the same sync command.
