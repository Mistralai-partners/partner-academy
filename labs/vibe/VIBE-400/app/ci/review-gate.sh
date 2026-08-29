#!/usr/bin/env bash
# Headless CI review gate for Vibe Code.
#
# Two modes:
#   Offline (deterministic, used by verify and by CI unit tests):
#       ci/review-gate.sh ci/samples/approved.json
#       cat transcript.json | ci/review-gate.sh
#   Live (the reproducible pipeline command):
#       MISTRAL_API_KEY=... ci/review-gate.sh --live "Review the diff in app/. \
#         End with a line 'VERDICT: APPROVE' or 'VERDICT: REQUEST_CHANGES'."
#
# The live command bounds the run (--max-turns), pins a read-only reviewer
# agent (--agent ci-reviewer), grants temporary trust for the untrusted
# checkout (--trust), and emits machine-readable JSON (--output json). The
# gate parses the model's verdict into a CI exit code:
#   0 = APPROVE, 1 = REQUEST_CHANGES, 3 = broken run (never a silent pass).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" = "--live" ]; then
  PROMPT="${2:?usage: review-gate.sh --live \"<prompt>\"}"
  : "${MISTRAL_API_KEY:?set MISTRAL_API_KEY for a live run}"
  # Bounded, read-only, trusted-for-this-run, JSON out. --auto-approve lets the
  # read-only tools run non-interactively in -p mode.
  JSON="$(vibe -p "$PROMPT" \
      --agent ci-reviewer \
      --output json \
      --max-turns 4 \
      --trust \
      --auto-approve)" || { echo "gate: vibe run failed" >&2; exit 3; }
  printf '%s' "$JSON" | python3 "$HERE/parse_verdict.py"
  exit $?
fi

# Offline mode: transcript from a file arg, else from stdin.
if [ -n "${1:-}" ] && [ -f "${1:-}" ]; then
  python3 "$HERE/parse_verdict.py" < "$1"
else
  python3 "$HERE/parse_verdict.py"
fi
exit $?
