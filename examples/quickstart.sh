#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Offline first-search walkthrough (NFR-013). Requires `lodestone` on PATH.
set -euo pipefail

if ! command -v lodestone >/dev/null 2>&1; then
  echo "lodestone is not on PATH" >&2
  exit 1
fi

ROOT="$(mktemp -d "${TMPDIR:-/tmp}/lodestone-quickstart.XXXXXX")"
cleanup() { rm -rf "$ROOT"; }
trap cleanup EXIT
cd "$ROOT"

mkdir -p docs
cat > docs/manifest.md <<'EOF'
# Manifest restore
ERR_MANIFEST_TIMEOUT occurs when restoring a checkpoint over NFS.
EOF

lodestone init
lodestone source add docs --kind files --path ./docs
lodestone sync --offline
lodestone search "ERR_MANIFEST_TIMEOUT" --explain --offline
