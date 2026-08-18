#!/usr/bin/env python3
"""post_agent gate hook (Vibe Code wire protocol).

Fires after each assistant turn completes. It SHOULD record a turn boundary in
``audit.log``. A post_agent hook may also DENY, which injects ``reason`` back
as a retry user message (capped at 3 retries per hook per turn).

Constraints: post_agent hooks CANNOT use ``match`` or ``strict``. The stdin
payload has NO tool_* fields, only the session context and
hook_event_name="post_agent".

SYMPTOM: turn boundaries never appear in audit.log.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw)
    except json.JSONDecodeError:
        print("could not parse post_agent invocation", file=sys.stderr)
        return 1

    # TODO(Task 1): append a turn-boundary line to audit.log, e.g.
    #   "--- turn end (session <first 8 chars of session_id>) ---\n"
    _ = p

    return 0


if __name__ == "__main__":
    sys.exit(main())
