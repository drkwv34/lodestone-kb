# Connectors

Lodestone ingests through named sources in `lodestone.toml`. Built-in kinds
are `files` and `threads`. Other kinds load the `lodestone.connectors`
entry-point group.

## Files (`kind = "files"`)

Walks a directory. Nested `.gitignore` rules apply. Binaries and oversize
files are skipped with a logged reason. Path jail: the resolved path must
stay inside the configured root (`..` and escaping symlinks are refused).

```sh
lodestone source add wiki --kind files --path ./docs --exclude 'drafts/**'
```

Markdown/text keep a `doc` parent plus heading `section` children. Code
keeps a `code_file` parent with a signature outline and `code` children.
Supported languages: Python, JavaScript, TypeScript, Go, Java, C, C++, Rust.
Chunks target 400 tokens and never exceed 800 (configurable). Unchanged
normalised content produces zero record writes. Deleted files are
tombstoned; `sync --prune` purges them.

## Threads (`kind = "threads"`)

One JSONL file, one JSON object per line. Convert a Slack workspace export:

```sh
python examples/slack_export_to_jsonl.py /path/to/slack-export -o threads.jsonl
lodestone source add chat --kind threads --path ./threads.jsonl
lodestone sync --offline
```

Qualifying same-author bursts become `kind=burst` children with a context
prefix. A changed thread is replaced atomically (old bursts go away).

## Plugins

Register a class on the `lodestone.connectors` entry-point group. The entry
name is the source `kind`. `discover(config)` must yield items with
`ext_id`, `kind_hint`, `text`, `metadata`, and `updated_at`.

`examples/plugin_demo/` is a complete plugin of at most 60 lines (`kind =
"notes"`, `*.note` files). Install it with
`pip install -e examples/plugin_demo` or load it from tests.

```toml
[[sources]]
name = "notes"
kind = "notes"
path = "./notes"
```

See [examples/plugin_demo/README.md](../examples/plugin_demo/README.md).
