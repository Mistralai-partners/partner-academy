#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for all four WFLOW-TSE1 tasks.
# T1/T2 are structural checks through the real mistralai-workflows SDK; T3/T4 run live logic
# offline. No Mistral API key is required.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uv run --no-project \
  --with 'mistralai-workflows[mistralai]==3.10.0' \
  python "$ROOT/verify/checks.py" "$DIR"
