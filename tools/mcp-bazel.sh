#!/usr/bin/env bash
# MCP stdio entrypoint via the hermetic Bazel target (//pdf_toolkit/mcp_server:server).
# Claude Desktop spawns servers with no cwd and a GUI PATH — fix both, keep stdout
# clean for the MCP stream (bazel progress goes to stderr; we silence UI noise too).
# Trade-off vs tools/mcp.sh: hermetic deps, but cold starts pay a build (seconds
# when warm, minutes on first run — prebuild with `bazel build //pdf_toolkit/mcp_server:server`).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BAZEL="${BAZEL:-/opt/homebrew/bin/bazel}"
cd "$ROOT"
exec "$BAZEL" run --noshow_progress --ui_event_filters=-info,-stdout \
  //pdf_toolkit/mcp_server:server
