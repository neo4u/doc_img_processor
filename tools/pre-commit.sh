#!/usr/bin/env bash
# Pre-commit gate: lint → format → types → tests → BUILD drift → graph refresh.
# Run directly, via `bazel run //:pre-commit`, or as .git/hooks/pre-commit
# (tools/install-hooks.sh). Fails fast on the first broken check.
set -euo pipefail

# Resolve symlinks first — as .git/hooks/pre-commit, BASH_SOURCE is the symlink
# and dirname would land in .git/ (readlink -f follows it back to tools/).
SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
ROOT="$(cd "$(dirname "$SELF")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin"

[ -x "$PY/python" ] || { echo "no .venv — run tools/venv.sh first"; exit 1; }

echo "── 1/5 ruff check"
"$PY/ruff" check pdf_toolkit

echo "── 2/5 ruff format --check"
"$PY/ruff" format --check pdf_toolkit

echo "── 3/5 mypy"
"$PY/mypy" pdf_toolkit

echo "── 4/5 pytest (+coverage floor)"
"$PY/pytest" --cov=pdf_toolkit --cov-report=term-missing:skip-covered --cov-fail-under=75 -q

echo "── 5/5 gazelle BUILD drift"
if command -v bazel >/dev/null 2>&1; then
  bazel run --ui_event_filters=-info,-stdout --noshow_progress //:gazelle -- -mode=diff \
    || { echo "BUILD files out of date — run: bazel run //:gazelle"; exit 1; }
else
  echo "  (bazel not installed — skipped; install bazelisk to enable)"
fi

echo "── 6/6 knowledge graph refresh (graphify)"
if command -v graphify >/dev/null 2>&1 && [ -f "$ROOT/graphify-out/graph.json" ] && [ "${SKIP_GRAPH:-}" != "1" ]; then
  graphify update "$ROOT" --no-cluster >/dev/null 2>&1 \
    && git -C "$ROOT" add graphify-out 2>/dev/null \
    || echo "  (graph update failed — commit proceeds; run 'graphify update .' manually)"
else
  echo "  (skipped: no graphify/graph.json or SKIP_GRAPH=1)"
fi

echo "✔ all pre-commit checks passed"
