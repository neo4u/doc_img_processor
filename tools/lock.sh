#!/usr/bin/env bash
# Recompile the platform pip locks from requirements(.dev).in via uv.
# Run after ANY edit to dependencies/python/requirements*.in, then tools/venv.sh.
# Both locks feed BOTH consumers: uv pip sync (venv.sh) and Bazel pip.parse.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/dependencies/python"

uv pip compile --quiet "$DIR/requirements.in" "$DIR/requirements-dev.in" \
  --python-version 3.13 --python-platform macos \
  -o "$DIR/requirements-darwin-aarch64.txt"
uv pip compile --quiet "$DIR/requirements.in" "$DIR/requirements-dev.in" \
  --python-version 3.13 --python-platform linux \
  -o "$DIR/requirements-linux-x86_64.txt"

echo "locks recompiled — now run: tools/venv.sh  (and bazel run //:gazelle_python_manifest.update if deps changed)"
