#!/usr/bin/env python3
"""post_agent gate hook (Vibe Code wire protocol).

Fires after each assistant turn completes. Records a turn boundary in
``audit.log``. A post_agent hook may also DENY, which injects ``reason`` back
as a retry user message (capped at 3 retries per hook per user turn) - useful
to force the agent to satisfy a policy before it is allowed to finish.

Constraints (grounded in vibe.core.hooks.models):
  post_agent hooks CANNOT use ``match`` or ``strict`` - both are tool-hook
  only. The stdin payload has NO tool_* fields, only the session context and
  hook_event_name="post_agent".
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
        print("could not parse post_agent invocation", file=sys.stderr)
        return 1

    session = str(p.get("session_id", "?"))[:8]
    pathlib.Path("audit.log").open("a", encoding="utf-8").write(
        f"--- turn end (session {session}) ---\n"
    )
    # Allow the turn to complete (empty stdout = passthrough).
    return 0


if __name__ == "__main__":
    sys.exit(main())
