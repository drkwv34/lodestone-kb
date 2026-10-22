# Provider presets

Lodestone talks to chat and embedding servers over OpenAI-compatible HTTP only
(`base_url`, `model`, `api_key_env`). Optional `json_mode` maps to
`response_format: json_object` when the server supports it. There are no
provider-specific clients.

API keys belong in environment variables named by `api_key_env`, never in TOML.

## Cerebras

```toml
schema_version = 1
[llm]
base_url = "https://api.cerebras.ai/v1"
model = "gpt-oss-120b"
api_key_env = "CEREBRAS_API_KEY"
json_mode = true
timeout_s = 60
```

## OpenAI

```toml
schema_version = 1
[llm]
base_url = "https://api.openai.com/v1"
model = "gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
json_mode = true
```

## Ollama

```toml
schema_version = 1
[llm]
base_url = "http://localhost:11434/v1"
model = "llama3.1"
api_key_env = ""
json_mode = false
[embed]
provider = "openai_compat"
base_url = "http://localhost:11434/v1"
model = "nomic-embed-text"
dim = 768
```
