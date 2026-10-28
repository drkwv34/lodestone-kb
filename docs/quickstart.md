# Quickstart

Time to first search from a source install is under five minutes on this
machine when following the offline walkthrough below (NFR-013). CI runs
`examples/quickstart.sh` so the commands stay executable.

## Requirements

- Python 3.11, 3.12, or 3.13
- SQLite with FTS5 (the python.org and GitHub Actions builds include it)
- Optional: `pip install 'lodestone-kb[vec]'` for sqlite-vec; brute-force
  cosine is used when the extra is absent

## Install

A published release will install with `pip install lodestone-kb`. This
repository is version `0.1.0rc1` and is not on PyPI. From a clone:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e '.[vec]'
lodestone --help
```

## Offline first search

```sh
lodestone init
lodestone doctor --offline
lodestone source add docs --kind files --path ./docs
lodestone sync --offline
lodestone search "ERR_MANIFEST_TIMEOUT" --explain
```

`init` is idempotent: a second run prints `already initialised` and keeps
existing TOML and records. `--offline` uses heuristic cards and the 256-d hash
embedder (deterministic, **not semantic**) and raises `OfflineError` if a
remote provider is requested.

`examples/quickstart.sh` creates a temp directory, writes a tiny `docs/` file
containing `ERR_MANIFEST_TIMEOUT`, then runs the same commands.

## Next commands

```sh
lodestone grep "ERR_MANIFEST_TIMEOUT"
lodestone who-knows "manifest"
lodestone recent --limit 5
lodestone ask "Why does restore stall?" --provider fake --offline
lodestone stats
lodestone search "ERR_MANIFEST_TIMEOUT" --json
```

Thread JSONL: convert a Slack export with
`examples/slack_export_to_jsonl.py`, then
`lodestone source add chat --kind threads --path ./threads.jsonl`.

MCP: [mcp.md](mcp.md). Benchmark: [bench.md](bench.md). Connectors:
[connectors.md](connectors.md).
