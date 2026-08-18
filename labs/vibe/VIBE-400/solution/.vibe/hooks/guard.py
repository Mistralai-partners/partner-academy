#!/usr/bin/env python3
"""pre_tool guard hook (Vibe Code wire protocol).

Reads the PreToolInvocation JSON on stdin, inspects the bash command in
``tool_input``, and DENIES the call when it matches a destructive pattern.

Wire protocol (grounded in vibe.core.hooks.models):
  stdin  : JSON object with session_id, transcript_path, cwd,
           hook_event_name="pre_tool", tool_name, tool_call_id, tool_input.
  stdout : exit 0 + JSON. decision="deny" blocks the tool and returns
           ``reason`` to the model as the tool error. Empty stdout = allow
           (passthrough). Non-zero exit / bad JSON = failure; because this
           hook is declared strict=true, a failure escalates to a denial.
"""
from __future__ import annotations

import json
import re
import sys

# Commands that must never run non-interactively, even under `always`.
DESTRUCTIVE = re.compile(
    r"\brm\s+-rf\b|\bgit\s+push\b|\bgit\s+reset\s+--hard\b|\bcurl\b.*\|\s*sh\b|>\s*/dev/sd",
)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed payload: fail loudly. strict=true turns this into a deny.
        print("could not parse pre_tool invocation", file=sys.stderr)
        return 1

    command = str(payload.get("tool_input", {}).get("command", ""))

    if DESTRUCTIVE.search(command):
        # Structured denial: exit 0 + JSON. The reason is surfaced to the model.
        json.dump(
            {
                "decision": "deny",
                "reason": (
                    "Blocked by guard hook: command matches a destructive "
                    f"pattern and is not allowed in automation: {command!r}"
                ),
            },
            sys.stdout,
        )
        return 0

    # Allow: empty stdout is an explicit passthrough (no rewrite, no deny).
    return 0


if __name__ == "__main__":
    sys.exit(main())
