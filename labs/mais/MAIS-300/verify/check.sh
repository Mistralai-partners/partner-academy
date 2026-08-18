#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
#
# Deterministic, OFFLINE acceptance check. Runs the pure-logic test suite against
# the chosen tree with the real mistralai SDK types (no network, no API key, no
# cost). Starter must FAIL; solution must PASS. The live_*.py scripts separately
# prove the same code paths against the real Mistral API.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$ROOT/$DIR"
if [ ! -d "$T/mais" ]; then
  echo "no such tree: $T"; exit 2
fi
echo "== Verifying $DIR =="
( cd "$T" && PYTHONPATH="$T" uv run --no-project \
    --with 'mistralai==1.9.11' --with pytest \
    python -m pytest -q tests )
rc=$?
if [ $rc -eq 0 ]; then
  echo "== $DIR: PASS (all 5 tasks complete — you traced and fixed every bug) =="
else
  echo "== $DIR: FAIL (rc=$rc) =="
  echo "   Each FAILED line above names the behavior that is still wrong — read it"
  echo "   as an incident report: what input the test gives, what it expects, and"
  echo "   what your code produced. That gap is the root cause. Fix it in mais/*.py"
  echo "   (find the '# BUG (Task N)' markers) and re-run."
fi
exit $rc
