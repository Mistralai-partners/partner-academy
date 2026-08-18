#!/bin/sh
# ci/review.sh (A4 starter STUB)
#
# This is the CI step that runs Vibe Code as a read-only reviewer over the pull
# request diff. In real CI this would run on the PR branch and post the summary as a
# comment. Here you just prove the run is safe.
#
# YOUR JOB: replace the placeholder below with a GUARDED headless `vibe -p` command.
# Pick ONE guard:
#   (a) a custom read-only agent profile invoked with --agent reviewer, or
#   (b) a pre-tool hook in .vibe/hooks.toml that denies write_file and edit.
#
# The command MUST run non-interactively (no prompts) and MUST be bounded on cost.
# See ../solution/review.sh for a completed reference of BOTH guards.

set -eu

DIFF_FILE="diff-to-review.patch"

if [ ! -f "$DIFF_FILE" ]; then
  echo "error: $DIFF_FILE not found; run this from the repo root" >&2
  exit 2
fi

# --- BEGIN placeholder: drop your guarded vibe command here ---------------------
#
# Headless mode is `vibe -p "PROMPT"`. Cost/turn flags only apply with -p:
#   --max-turns N        cap the number of agent turns
#   --max-price DOLLARS  hard cost ceiling (float), e.g. 0.05
#   --output json        dump the full conversation as a JSON array
# For non-interactive CI you also need to approve tool calls and trust the workdir:
#   --auto-approve       approve tool calls without prompting
#   --trust              trust this workdir for this invocation only (not persisted)
#
# Example shape (guard NOT yet applied; add --agent reviewer OR a hook):
#
#   vibe -p "Review the diff in $DIFF_FILE and summarize the risks" \
#     --output json --max-turns 6 --max-price 0.05 --auto-approve --trust \
#     > review-output.json
#
echo "TODO: replace this line with your guarded vibe -p command" >&2
exit 1
#
# --- END placeholder ------------------------------------------------------------

# Interpreting the result (uncomment once your command writes review-output.json):
#
# EXIT_CODE=$?
# A clean exit is code 0. A non-zero code means the run failed or was interrupted
# (for example, hitting --max-turns emits a <vibe_stop_event> marker in the output).
# The REAL safety proof is not the exit code alone. It is:
#   1. `git diff` is empty (nothing on the branch changed), and
#   2. the JSON array contains no write_file/edit tool calls (branch a), or the
#      pre-tool hook denied them (branch b).
# See ../VERIFY.md for the exact checks.
