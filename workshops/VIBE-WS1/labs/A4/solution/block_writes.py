#!/usr/bin/env python3
"""Pre-tool hook that denies every write_file / edit tool call.

Hook contract (Vibe Code, verified against vibe 2.24.0):
  - A pre_tool hook runs BEFORE the permission prompt.
  - The invocation arrives as a JSON object on STDIN. For pre_tool it includes at
    least: session_id, transcript_path, cwd, tool_name, tool_call_id, tool_input.
  - To act, the hook must EXIT 0 and print a single JSON object on STDOUT shaped like
    {"decision": "allow" | "deny", "reason": "..."}. `decision` defaults to "allow".
    A "deny" blocks the tool call and `reason` is returned to the model as an error.
  - Empty stdout is a no-op. Non-zero exit or malformed JSON is a failure, escalated
    to a denial only when the hook is configured with strict = true.

This script fires only for write_file / edit because that is the `match` in
hooks.toml. It therefore denies unconditionally. It still reads and parses stdin so
that a malformed payload surfaces as a hook error rather than a silent allow.

Pure standard library only (json, sys). No external dependencies.
"""

import json
import sys


def main():
    raw = sys.stdin.read()
    # Parse the invocation so a broken payload fails loudly instead of allowing.
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        # Malformed input: exit non-zero so the runtime treats it as a hook failure.
        sys.stderr.write(f"block_writes: could not parse hook JSON: {exc}\n")
        return 1

    tool_name = payload.get("tool_name", "unknown")
    decision = {
        "decision": "deny",
        "reason": (
            f"Blocked '{tool_name}': this run is a read-only reviewer. "
            "Write and edit tools are denied by policy (posture, not prompt)."
        ),
    }
    sys.stdout.write(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
