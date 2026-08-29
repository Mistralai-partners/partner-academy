#!/usr/bin/env python3
"""post_tool audit hook (Vibe Code wire protocol).

Fires after any tool body executes and appends one audit line per call to
``audit.log`` in the project root. This is the marker the verifier checks to
prove the hook actually ran.

Wire protocol (grounded in vibe.core.hooks.models.PostToolInvocation):
  stdin  : JSON with tool_name, tool_call_id, tool_input, tool_status
           ("success" | "failure" | "cancelled"), tool_output,
           tool_output_text, tool_error, duration_ms, plus the session fields.
  stdout : empty => passthrough. Optionally exit 0 + JSON with
           hook_specific_output.additional_context to APPEND text to the
           tool result the model sees.

Key firing rule: post_tool fires ONLY when the tool body executed. If a
pre_tool hook denied the call, the body never ran, so no post_tool audit line
is written for it.
"""
from __future__ import annotations

import json
import pathlib
import sys


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw)
    except json.JSONDecodeError:
        print("could not parse post_tool invocation", file=sys.stderr)
        return 1

    line = "{name} status={status} {ms:.0f}ms\n".format(
        name=p.get("tool_name", "?"),
        status=p.get("tool_status", "?"),
        ms=float(p.get("duration_ms", 0) or 0),
    )
    # Append to the project-root audit log (executor cwd == project root).
    pathlib.Path("audit.log").open("a", encoding="utf-8").write(line)

    # Passthrough: do not alter the tool result.
    return 0


if __name__ == "__main__":
    sys.exit(main())
