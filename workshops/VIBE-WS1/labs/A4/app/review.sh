#!/bin/sh
# review.sh: completed reference CI step (A4 solution)
#
# Shows BOTH guarded approaches. In real CI you would pick ONE. Every flag here is
# within the verified vibe 2.24.0 ground truth. Live runs need MISTRAL_API_KEY and
# will call the paid API.

set -eu

DIFF_FILE="diff-to-review.patch"

if [ ! -f "$DIFF_FILE" ]; then
  echo "error: $DIFF_FILE not found; run this from the repo root" >&2
  exit 2
fi

# ==============================================================================
# Branch (a): custom read-only agent profile
# ==============================================================================
# Requires ~/.vibe/agents/reviewer.toml (copy app/reviewer.toml there first).
# The reviewer agent allow-lists read_file + grep, so write_file/edit/bash do not
# exist for it. --max-price caps spend; --max-turns caps work; --trust trusts this
# workdir for this invocation only; --auto-approve stops it blocking on prompts.

echo "== Branch (a): --agent reviewer =="
vibe -p "Review the diff in $DIFF_FILE and summarize the risks" \
  --agent reviewer \
  --output json \
  --max-turns 6 \
  --max-price 0.05 \
  --auto-approve \
  --trust \
  > review-agent.json

echo "agent run exit code: $?"
# Proof of safety (see VERIFY.md): review-agent.json parses as a JSON array, contains
# no write_file/edit tool calls, and `git diff` is empty.

# ==============================================================================
# Branch (b): pre-tool hook that denies writes
# ==============================================================================
# Requires .vibe/hooks.toml pointing at an ABSOLUTE path to block_writes.py.
# Here we deliberately ask the model to EDIT a file. The hook denies write_file/edit,
# so the edit is blocked while the run still completes cleanly. This proves the guard
# fires under an adversarial prompt, not just a cooperative one.

echo "== Branch (b): pre-tool hook =="
vibe -p "Bump __version__ in src/release_tools/version.py to 1.5.0 by editing the file" \
  --output json \
  --max-turns 6 \
  --max-price 0.05 \
  --auto-approve \
  --trust \
  > review-hook.json

echo "hook run exit code: $?"
# Proof of safety (see VERIFY.md): the deny reason from block_writes.py appears in the
# review-hook.json message stream, and `git diff` is empty (version.py unchanged).
