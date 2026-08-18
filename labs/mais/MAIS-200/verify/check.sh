#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for MAIS-200. Runs each task script against the
# live Mistral API with the pinned SDK (mistralai==1.9.11). A task PASSES when its
# script exits 0. Starter FAILS until you complete each task; solution PASSES.
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

RUN() { uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python "$1"; }

pass=0; fail=0
echo "== Verifying $DIR =="
for f in t1_reliable_agent.py t2_tools_function_result.py t3_document_to_structured.py \
         t4_rag_knowledge_base.py t5_guardrails_moderation.py; do
  if RUN "$T/$f" >"/tmp/mais200_${DIR}_${f}.log" 2>&1; then
    echo "  PASS: $f"; pass=$((pass+1))
  else
    echo "  FAIL: $f (see /tmp/mais200_${DIR}_${f}.log)"; fail=$((fail+1))
  fi
done
echo "== $DIR: $pass passed, $fail failed =="
exit $fail
