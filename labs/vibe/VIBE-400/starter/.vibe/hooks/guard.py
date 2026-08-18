#!/usr/bin/env python3
"""pre_tool guard hook (Vibe Code wire protocol).

Reads the PreToolInvocation JSON on stdin. It SHOULD deny destructive shell
commands, but right now it lets everything through.

Wire protocol:
  stdin  : JSON with hook_event_name="pre_tool", tool_name, tool_call_id,
           tool_input (a dict; for bash it has a "command" key).
  stdout : exit 0 + JSON. decision="deny" blocks the tool and returns
           ``reason`` to the model. Empty stdout = allow (passthrough).

SYMPTOM: a run using this hook will happily execute `rm -rf` - the guard
never denies anything.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("could not parse pre_tool invocation", file=sys.stderr)
        return 1

    command = str(payload.get("tool_input", {}).get("command", ""))

    # TODO(Task 1): inspect `command` and emit a structured denial
    #   {"decision": "deny", "reason": "..."}  on stdout (exit 0)
    # when it matches a destructive pattern (rm -rf, git push, curl | sh, ...).
    # Leave stdout empty to allow safe commands.
    _ = command

    return 0


if __name__ == "__main__":
    sys.exit(main())
