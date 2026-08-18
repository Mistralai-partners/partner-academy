#!/usr/bin/env python3
"""Turn a `vibe -p --output json` transcript into a CI exit code.

Reads the JSON array Vibe emits on stdin, finds the LAST assistant text
message, and reads its verdict line:

    VERDICT: APPROVE           -> exit 0  (gate passes)
    VERDICT: REQUEST_CHANGES   -> exit 1  (gate fails the build)

Anything else (no assistant message, no verdict line, unparseable JSON)
-> exit 3, so a broken run never silently "passes".

SYMPTOM: this gate exits 0 no matter what - it passes REQUEST_CHANGES
verdicts and even malformed transcripts. A gate that cannot fail is not a
gate.
"""
from __future__ import annotations

import sys

EXIT_APPROVE = 0
EXIT_CHANGES = 1
EXIT_ERROR = 3


def main() -> int:
    _ = sys.stdin.read()
    # TODO(Task 5): parse the transcript, find the last assistant message text,
    # match a line 'VERDICT: APPROVE' or 'VERDICT: REQUEST_CHANGES', and return
    # EXIT_APPROVE / EXIT_CHANGES accordingly. Return EXIT_ERROR when the
    # transcript is not valid JSON, has no assistant message, or has no verdict.
    print("gate: (stub) passing everything")
    return EXIT_APPROVE


if __name__ == "__main__":
    sys.exit(main())
