#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for all six WFLOW-400 tasks.
# Structural checks use the real mistralai-workflows SDK; Task 3 runs live AES-GCM crypto.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec uv run --no-project \
  --with 'mistralai-workflows==3.10.0' \
  --with 'mistralai[workflow-payload-encryption]' \
  python "$ROOT/verify/checks.py" "$DIR"
