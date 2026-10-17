# SPDX-License-Identifier: Apache-2.0
"""Validated architecture 3.1 configuration; paths belong to the config directory."""

from __future__ import annotations

import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator

PositiveInt = Annotated[int, Field(gt=0)]
NonNegative = Annotated[float, Field(ge=0)]
Lane = Literal["fts_raw", "fts_card", "fts_rare", "vec_card", "vec_chunk", "grep"]
Kind = Literal["doc", "section", "code_file", "code", "thread", "burst"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True, allow_inf_nan=False)


class Workspace(Model):
    db_path: Path = Path(".lodestone/index.db")
    default_project: str = Field(default="default", min_length=1)


class Prices(Model):
    input: NonNegative = 0
    output: NonNegative = 0
    as_of: date | None = None


class Endpoint(Model):
    base_url: HttpUrl
    api_key_env: str = ""

    @field_validator("api_key_env")
    @classmethod
    def environment_name(cls, value: str) -> str:
        if value and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("must be an environment variable name")
        return value

    @field_validator("base_url")
    @classmethod
    def no_inline_credentials(cls, value: HttpUrl) -> HttpUrl:
        if value.username or value.password or value.query or value.fragment:
            raise ValueError("credentials and query parameters are forbidden; use api_key_env")
        return value


class LLM(Endpoint):
    base_url: HttpUrl = HttpUrl("https://api.cerebras.ai/v1")
    model: str = Field(default="gpt-oss-120b", min_length=1)
    api_key_env: str = "CEREBRAS_API_KEY"
    timeout_s: Annotated[float, Field(gt=0)] = 60
    max_retries: Annotated[int, Field(ge=0)] = 4
    max_concurrency: PositiveInt = 4
    json_mode: bool = True
    prices: Prices = Field(default_factory=Prices)


class Embed(Endpoint):
    base_url: HttpUrl = HttpUrl("http://localhost:11434/v1")
    provider: Literal["none", "openai_compat", "hash"] = "none"
    model: str = Field(default="nomic-embed-text", min_length=1)
    dim: PositiveInt = 768
    source: Literal["card", "raw", "both"] = "card"
    batch_size: PositiveInt = 64


class Chunks(Model):
    target_tokens: PositiveInt = 400
    max_tokens: PositiveInt = 800
    chars_per_token: PositiveInt = 4
    contextualize: bool = False


class Cards(Model):
    enabled: bool = True
    kinds: list[Kind] = Field(default=["thread", "doc", "code_file"])
    prompt_version: str = "card.v1"
    max_input_chars: PositiveInt = 24000


class Bursts(Model):
    idf_min: NonNegative = 4
    min_chars: PositiveInt = 200
    w_idf: NonNegative = 1
    w_len: NonNegative = 1
    w_react: NonNegative = 1
    threshold: NonNegative = 1


class Decay(Model):
    half_life_days: NonNegative = 0
    floor: Annotated[float, Field(ge=0, le=1)] = 0


class Retrieval(Model):
    lanes: list[Lane] = Field(
        default=["fts_raw", "fts_card", "fts_rare", "vec_card", "vec_chunk", "grep"]
    )
    weights: dict[Lane, NonNegative] = Field(
        default={
            "fts_raw": 1,
            "fts_card": 1,
            "fts_rare": 0.7,
            "vec_card": 1,
            "vec_chunk": 0.7,
            "grep": 0.5,
        }
    )
    rrf_k: PositiveInt = 60
    candidate_pool: PositiveInt = 20
    max_per_source: PositiveInt = 3
    rerank: bool = False
    rerank_keep: PositiveInt = 10
    expand: Annotated[int, Field(ge=0)] = 1
    expand_max_chars: PositiveInt = 4000
    rare_idf: NonNegative = 4
    rare_df_ratio: Annotated[float, Field(ge=0, le=1)] | None = None
    decay: dict[Kind, Decay] = Field(
        default={
            "thread": Decay(half_life_days=120, floor=0.4),
            "doc": Decay(),
            "code": Decay(),
        }
    )


class Ask(Model):
    max_rounds: PositiveInt = 3
    planner_model: str = ""
    synth_model: str = ""


class Log(Model):
    store_queries: bool = False
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class Source(Model):
    name: str = Field(min_length=1)
    kind: Literal["files", "threads"]
    path: Path
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    max_file_bytes: PositiveInt = 1024 * 1024
    refresh: Literal["manual"] = "manual"
    channel: str | None = None


class Project(Model):
    name: str = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)


class Config(Model):
    schema_version: Literal[1] = 1
    workspace: Workspace = Field(default_factory=Workspace)
    llm: LLM | None = None
    embed: Embed = Field(default_factory=Embed)
    chunks: Chunks = Field(default_factory=Chunks)
    cards: Cards = Field(default_factory=Cards)
    bursts: Bursts = Field(default_factory=Bursts)
    retrieval: Retrieval = Field(default_factory=Retrieval)
    ask: Ask = Field(default_factory=Ask)
    log: Log = Field(default_factory=Log)
    sources: list[Source] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=lambda: [Project(name="default")])

    def resolve_paths(self, directory: Path) -> Self:
        self.workspace.db_path = (directory / self.workspace.db_path).resolve()
        for source in self.sources:
            source.path = (directory / source.path).resolve()
        return self


class ConfigError(ValueError):
    """Safe, actionable configuration error without input values."""


def error_path(location: tuple[int | str, ...]) -> str:
    result = ""
    for part in location:
        result += f"[{part}]" if isinstance(part, int) else ("." if result else "") + part
    return result


def load_config(path: Path) -> Config:
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        return Config.model_validate(data).resolve_paths(path.resolve().parent)
    except ValidationError as exc:
        # Pydantic messages may include user input; report paths and stable error types only.
        details = "; ".join(
            f"{error_path(error['loc'])}: {error['type']}"
            for error in exc.errors(include_input=False, include_context=False, include_url=False)
        )
        raise ConfigError(details) from None
    except tomllib.TOMLDecodeError:
        raise ConfigError("Invalid TOML; check syntax in configuration file") from None
    except OSError:
        raise ConfigError(f"Cannot read configuration: {path}") from None


def redact(value: object) -> object:
    """Recursively redact key/token/secret fields without looking up any environment values."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if re.search(r"key|token|secret", str(key), re.I) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


DEFAULT_TOML = """# SPDX-License-Identifier: Apache-2.0
# Offline defaults. Provider keys belong in environment variables, never in this file.
schema_version = 1
[workspace]
db_path = ".lodestone/index.db"
default_project = "default"
[[projects]]
name = "default"
sources = []
"""
