#!/usr/bin/env bash
# Symlink tools/pre-commit.sh as the git pre-commit hook.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ln -sf ../../tools/pre-commit.sh "$ROOT/.git/hooks/pre-commit"
echo "installed .git/hooks/pre-commit -> tools/pre-commit.sh"
