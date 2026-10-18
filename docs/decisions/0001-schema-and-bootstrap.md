# Workspace foundation implementation decisions

The supplied specifications are preserved in `docs/spec/`. The user's
workspace-foundation scope takes precedence over later-feature examples and
document instructions.

1. Architecture 7.1 declares an external-content FTS column `norm` but its backing
   `records` table has `norm_text`. SQLite requires matching names. Migration 0001
   uses `norm_text` for that FTS column. Lexical-search queries/triggers must use that name.
   No FTS triggers or retrieval are implemented in the workspace foundation.
2. Connection PRAGMAs (WAL and foreign keys) are configured before migrations;
   `user_version` is stamped at the end of the same transaction as the DDL.
   This corrects the example's early version stamp and avoids WAL changes inside
   transactions. Evaluation tables are deferred as explicitly requested.
3. The README quickstart uses the editable source install and the three commands
   available today. Source connectors, SDK, MCP and benchmark examples are marked
   roadmap. Entry points for unimplemented connectors are deferred to their features.
4. The workspace foundation has no performance suite. The performance job is deferred
   until hybrid fusion; portability, quality, OpenSpec, build and license checks
   are blocking now.
5. Actual package verification on 2026-10-17: OpenSpec 1.14.3; hatchling 1.32.4;
   Typer 0.27.3; pydantic 2.14.1; MCP 2.3.0; pathspec 1.1.1; sqlite-vec 0.1.9.
   MCP APIs remain unimplemented until the MCP and ask feature.
6. Existing root commit `a29d735` is authored by Christian Agila but committed by
   GitHub <noreply@github.com>. History is preserved per the user's no-rewrite rule.
   All new commits use Christian as both author and committer. Evidence includes
   the root commit and reports this inherited exception explicitly.
