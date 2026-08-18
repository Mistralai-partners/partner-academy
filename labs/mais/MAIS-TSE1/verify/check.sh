#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for MAIS-TSE1. Tasks 1-2 run live against the
# Mistral API (Document AI extraction, embeddings + chat grounding); tasks 3-4
# are offline scoping decisions. A task PASSES when its script exits 0.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$ROOT/$DIR"

# Load MISTRAL_API_KEY from a local .env if present; otherwise use the environment.
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
if [ -z "${MISTRAL_API_KEY:-}" ]; then
  echo "ERROR: MISTRAL_API_KEY not set (create $ROOT/.env from .env.example or export it)."
  exit 2
fi

RUN() { uv run --no-project --with 'mistralai==1.9.11' --with pydantic --with python-dotenv python "$1"; }

pass=0; fail=0
echo "== Verifying $DIR =="
for f in t1_docai_extract.py t2_rag_grounding.py t3_scope_surface.py t4_scope_multiagent.py; do
  if RUN "$T/$f" >"/tmp/maistse1_${DIR}_${f}.log" 2>&1; then
    echo "  PASS: $f"; pass=$((pass+1))
  else
    echo "  FAIL: $f (see /tmp/maistse1_${DIR}_${f}.log)"; fail=$((fail+1))
  fi
done
echo "== $DIR: $pass passed, $fail failed =="
exit $fail
