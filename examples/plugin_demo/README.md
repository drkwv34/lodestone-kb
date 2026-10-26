# Plugin demo

A connector of at most 60 lines that registers on the `lodestone.connectors`
entry-point group as `notes`. Each `*.note` file under the source path becomes
one document record.

```toml
[[sources]]
name = "notes"
kind = "notes"
path = "./notes"
```

Install the extra in a workspace (`pip install -e examples/plugin_demo`) or
rely on tests that load the entry point from this directory.
