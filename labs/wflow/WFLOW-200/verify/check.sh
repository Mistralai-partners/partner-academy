#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for all five WFLOW-200 tasks.
# Structural checks use the real mistralai-workflows SDK; pure logic runs live offline.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uv run --no-project \
  --with 'mistralai-workflows[mistralai]==3.10.0' \
  python "$ROOT/verify/checks.py" "$DIR"
