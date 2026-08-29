#!/usr/bin/env python3
"""Turn a `vibe -p --output json` transcript into a CI exit code.

Reads the JSON array Vibe emits (list of message/reasoning/tool entries) on
stdin, finds the LAST assistant text message, and reads its verdict line:

    VERDICT: APPROVE           -> exit 0  (gate passes)
    VERDICT: REQUEST_CHANGES   -> exit 1  (gate fails the build)

Anything else (no assistant message, no verdict line, unparseable JSON)
-> exit 3, so a broken run never silently "passes".
"""
from __future__ import annotations

import json
import re
import sys

EXIT_APPROVE = 0
EXIT_CHANGES = 1
EXIT_ERROR = 3

VERDICT = re.compile(r"^VERDICT:\s*(APPROVE|REQUEST_CHANGES)\s*$", re.MULTILINE)


def _last_assistant_text(entries: list) -> str | None:
    for entry in reversed(entries):
        if entry.get("type") == "message" and entry.get("role") == "assistant":
            parts = [
                c.get("text", "")
                for c in entry.get("content", [])
                if c.get("type") == "text"
            ]
            text = "".join(parts).strip()
            if text:
                return text
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"gate: transcript is not valid JSON: {e}", file=sys.stderr)
        return EXIT_ERROR
    if not isinstance(entries, list):
        print("gate: expected a JSON array of message entries", file=sys.stderr)
        return EXIT_ERROR

    text = _last_assistant_text(entries)
    if text is None:
        print("gate: no assistant message in transcript", file=sys.stderr)
        return EXIT_ERROR

    m = VERDICT.search(text)
    if not m:
        print("gate: no 'VERDICT: APPROVE|REQUEST_CHANGES' line found", file=sys.stderr)
        return EXIT_ERROR

    verdict = m.group(1)
    print(f"gate: verdict = {verdict}")
    return EXIT_APPROVE if verdict == "APPROVE" else EXIT_CHANGES


if __name__ == "__main__":
    sys.exit(main())
