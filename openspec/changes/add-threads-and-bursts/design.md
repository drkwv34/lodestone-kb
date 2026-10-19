# Design

## Context

Records already allow `kind` values `thread` and `burst`. Distillation already accepts `thread` in `cards.kinds` and heuristic cards already take an optional message list. Sync currently rejects non-file sources.

## Goals / Non-Goals

**Goals:**
- Stream one JSONL object per thread; skip bad lines with numbers; store UTC timestamps.
- One parent record per thread; children are qualifying bursts only.
- Atomic replace of parent, card, bursts and embeddings when content changes.
- Burst gate using configurable SRS defaults; searchable `kind=burst` rows.
- Thread cards via FakeLLM or heuristic last-message resolution.

**Non-Goals:**
- Live Slack APIs, vector burst embeddings, fusion/decay, MCP, connector plugins.

## Decisions

1. Naive ISO-8601 timestamps (no offset, no `Z`) are rejected and the line is skipped. Offsets and `Z` convert to UTC.
2. No new migration: `thread`/`burst` kinds, `context_prefix`, `author` and `authors_json` already exist. Existing migrations stay immutable.
3. Burst IDF is read from `term_stats` after the parent upsert in the same transaction. On a tiny corpus the IDF signal is usually below `idf_min=4.0`; length and reactions still pass a burst under default `threshold=1.0`.
4. Changed threads write the parent, card, bursts and embedding deletes in one SQLite transaction. Unchanged threads skip record writes and only refresh cards from cache.
5. `RawItem.messages` carries parsed messages; files leave it `None`. Message payloads are stored as a JSON string in record metadata so `metadata` stays `dict[str, str]`.

## Risks / Trade-offs

- Default IDF 4.0 needs a large N to fire; tests inject IDF and cover length/reaction signals independently.
- Burst `ext_id` uses the source group index (`thread_id#burst:N`); filtered groups leave gaps, which is acceptable because a thread replace deletes previous bursts.
