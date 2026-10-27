# Privacy and data flow

Lodestone stays local by default. API keys are read from the environment and
never stored in `lodestone.toml`. Structured logs omit secrets and raw record
text. `--offline` / `offline = true` replaces remote providers with the hash
embedder and heuristic cards and makes no network connections.

There is no telemetry. `config show` redacts fields whose names contain
key/token/secret. `LODESTONE_LLM_API_KEY` and `LODESTONE_EMBED_API_KEY`
override configured environment references at runtime without entering TOML.

## Data-flow table (NFR-010)

| Command | Leaves the machine | Stays local |
|---|---|---|
| `init`, `doctor`, `config show`, `stats`, `cost` | Nothing | Config, SQLite, probes |
| `sync` (offline / no `llm`) | Nothing | Source files, SQLite, heuristic cards |
| `sync` with configured chat | Card-prompt text (record raw text truncated to `cards.max_input_chars`) | SQLite, FTS, cost log |
| `sync` with `embed.provider=openai_compat` | Embedding input (`embed.source`: card text, raw, or both) | Vectors in SQLite |
| `search` (no rerank) | Nothing | FTS / optional local vectors |
| `search --rerank` | Query plus candidate snippets (≤ 1,200 characters each) | Fused order fallback on error |
| `ask` | Planner/synthesis prompts over retrieved snippets | Evidence packets, citations |
| `mcp` | Nothing unless a tool uses rerank | Read-only SQLite (`mode=ro`) |
| `bench` offline strategies | Nothing | Isolated temp indexes, FakeLLM / hash embedder |
| `reindex --lanes fts\|cards\|vec` | Nothing when `--offline`; vec/cards use local stored text | SQLite derived tables |

Default config does not send full corpus text. Only card prompts and rerank
snippets go to a configured provider when those features are enabled.

Keep workspace files (`.lodestone/`, `lodestone.toml` if it names private
paths) out of version control unless you intend to share them.
