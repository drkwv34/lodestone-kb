# Lexical-only scale (NFR-004)

Measured on 2026-10-26. Numbers are from one run of `scripts/scale_lexical.py`
on this machine. The script bulk-inserts 200,000 small documents into the
current SQLite schema (per-row FTS triggers dropped for the load), rebuilds
FTS and `record_terms`, then searches `fts_raw`.

## Hardware

- Host: Linux 6.12.94+ x86_64 (`uname -a`: `Linux cursor 6.12.94+ #1 SMP PREEMPT_DYNAMIC Mon Oct 19 22:12:29 UTC 2026 x86_64`)
- CPU: Intel(R) Xeon(R) Processor, 4 logical CPUs (`nproc` = 4)
- Memory: 16,387,280 kB MemTotal (~15.6 GiB)
- Python: 3.12.3
- SQLite: 3.45.1 (FTS5)

## Command

```text
$ LODESTONE_SCALE_N=200000 LODESTONE_SCALE_DIR=/tmp/lodestone-scale-fast-4680 \
    python3 scripts/scale_lexical.py
records=200000
insert_s=4.73
db_bytes=146984960
db_gb=0.1369
search_ms=19.16
search_hits=10
rss_mb=54.1
```

## Result vs NFR-004

| Limit | Measured |
|---|---|
| 200,000 records | 200,000 non-tombstoned rows |
| DB <= 2 GB without embeddings | 0.1369 GB (146,984,960 bytes) |
| Search RSS <= 500 MB | 54.1 MB `ru_maxrss` |

Search query: `SCALE_TOKEN_3` on `fts_raw`, limit 10, 10 hits.

This is a lexical-only index (no embeddings, no LLM cards). It is not a
full per-file ingest of 200k source files.
