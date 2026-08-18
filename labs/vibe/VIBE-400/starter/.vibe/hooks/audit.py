#!/usr/bin/env python3
"""post_tool audit hook (Vibe Code wire protocol).

Fires after any tool body executes. It SHOULD append one line per executed
tool call to ``audit.log`` in the project root - the run trail an operator
reads after the fact. Right now it writes nothing.

Wire protocol (post_tool stdin): tool_name, tool_call_id, tool_input,
tool_status ("success"|"failure"|"cancelled"), tool_output, tool_output_text,
tool_error, duration_ms, plus the session fields.

SYMPTOM: after a run, audit.log does not exist - there is no record of what
the agent did.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw)
    except json.JSONDecodeError:
        print("could not parse post_tool invocation", file=sys.stderr)
        return 1

    # TODO(Task 1): append a line such as
    #   "<tool_name> status=<tool_status> <duration_ms>ms\n"
    # to audit.log in the project root (the hook runs with cwd == project root).
    _ = p

    return 0


if __name__ == "__main__":
    sys.exit(main())
