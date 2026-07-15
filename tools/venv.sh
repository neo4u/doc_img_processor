#!/usr/bin/env bash
# Bootstrap/refresh the project venv at .venv using uv, from the PLATFORM LOCK
# (not requirements.in — the venv must match what Bazel's pip.parse resolves).
# Idempotent: safe at every session start (hclaude hook, cli.sh, mcp.sh, //:venv).
# Regenerate locks with tools/lock.sh after editing requirements*.in.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
STAMP="$VENV/.req-stamp"
PYTHON_VERSION="3.13"   # matches locks, Bazel toolchain, ruff target

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) LOCK="$ROOT/dependencies/python/requirements-darwin-aarch64.txt" ;;
  Linux-x86_64) LOCK="$ROOT/dependencies/python/requirements-linux-x86_64.txt" ;;
  *) echo "no lock for $(uname -s)-$(uname -m) — add one via tools/lock.sh" >&2; exit 1 ;;
esac

command -v uv >/dev/null || { echo "uv not found — install: https://docs.astral.sh/uv/" >&2; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  uv venv --quiet --python "$PYTHON_VERSION" "$VENV"
fi

# Re-sync only when the lock changed since the last successful sync.
current="$(shasum -a 256 "$LOCK" | cut -d' ' -f1)"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$current" ]; then
  uv pip sync --quiet --python "$VENV/bin/python" "$LOCK"   # exact: adds AND removes
  echo "$current" > "$STAMP"
  echo "venv: synced to $(basename "$LOCK")"
else
  echo "venv: up to date"
fi
