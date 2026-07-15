#!/usr/bin/env bash
# Single CLI entrypoint: tools/cli.sh <subcommand> [args...]
# Daily driver = project venv (fast, works without bazel; bootstraps if missing).
# Hermetic alternative for CI/verification: bazel run //:py_cli -- <args>
# (bazel run executes from runfiles — pass absolute input paths there).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -x "$ROOT/.venv/bin/python" ] || "$ROOT/tools/venv.sh"
exec "$ROOT/.venv/bin/python" -m pdf_toolkit.cli.main "$@"
