#!/usr/bin/env bash
# MCP stdio entrypoint for contexts that spawn without the project cwd
# (Claude Desktop / cowork). Self-bootstraps the venv, fixes cwd, execs the server.
# IMPORTANT (stdio transport): nothing may print to stdout except the server —
# venv bootstrap output is routed to stderr.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -x "$ROOT/.venv/bin/python" ] || "$ROOT/tools/venv.sh" 1>&2
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -m pdf_toolkit.mcp_server.server
