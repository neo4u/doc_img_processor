#!/usr/bin/env bash
# Pre-commit gate: lint → format → types → tests → BUILD drift.
# Run directly, via `bazel run //:pre-commit`, or as .git/hooks/pre-commit
# (tools/install-hooks.sh). Fails fast on the first broken check.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin"

[ -x "$PY/python" ] || { echo "no .venv — run tools/venv.sh first"; exit 1; }

echo "── 1/5 ruff check"
"$PY/ruff" check pdf_toolkit

echo "── 2/5 ruff format --check"
"$PY/ruff" format --check pdf_toolkit

echo "── 3/5 mypy"
"$PY/mypy" pdf_toolkit

echo "── 4/5 pytest"
"$PY/pytest"

echo "── 5/5 gazelle BUILD drift"
if command -v bazel >/dev/null 2>&1; then
  bazel run --ui_event_filters=-info,-stdout --noshow_progress //:gazelle -- -mode=diff \
    || { echo "BUILD files out of date — run: bazel run //:gazelle"; exit 1; }
else
  echo "  (bazel not installed — skipped; install bazelisk to enable)"
fi

echo "✔ all pre-commit checks passed"
