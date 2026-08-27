#!/usr/bin/env python3
"""Self-check a change-plan against the required target symbols for lab A1.

Usage:
    python app/verify/plan_check.py PATH_TO_YOUR_PLAN.md

This script does not judge prose. It confirms your plan names the same target
files and entry points as the reference change-plan: the refund endpoint
handler, the refund domain function, the store, the idempotency concept, and the
test you would add. It is deliberately dependency free (standard library only).

Exit codes:
    0  PASS  (all required symbols present)
    1  FAIL  (one or more required symbols missing, or empty file)
    2  usage or read error
"""

from __future__ import annotations

import sys

# Each entry: (human label, tuple of acceptable substrings). A requirement is
# satisfied if ANY of its substrings appears in the plan, matched
# case-insensitively.
REQUIRED = [
    ("API handler file (api.py)", ("api.py",)),
    ("refund endpoint handler (handle_refund)", ("handle_refund",)),
    ("refund domain module (refunds.py)", ("refunds.py",)),
    ("refund domain function (process_refund)", ("process_refund",)),
    ("payment/refund store module (store.py)", ("store.py",)),
    ("idempotency concept (idempotency key)", ("idempoten",)),
    ("test to add (tests/test_refunds.py)", ("tests/test_refunds.py", "test_refunds.py")),
]


def check_plan(text: str) -> list[str]:
    """Return the list of missing requirement labels for the given plan text."""
    haystack = text.lower()
    missing = []
    for label, alternatives in REQUIRED:
        if not any(alt.lower() in haystack for alt in alternatives):
            missing.append(label)
    return missing


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python plan_check.py PATH_TO_YOUR_PLAN.md", file=sys.stderr)
        return 2

    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"FAIL: cannot read plan file {path!r}: {exc}", file=sys.stderr)
        return 2

    total = len(REQUIRED)

    if not text.strip():
        print(f"FAIL: plan file {path!r} is empty.")
        print(f"Missing all {total} required symbols:")
        for label, _ in REQUIRED:
            print(f"  - {label}")
        return 1

    missing = check_plan(text)
    found = total - len(missing)
    if missing:
        print(f"FAIL: plan names {found}/{total} required symbols.")
        print("Missing:")
        for label in missing:
            print(f"  - {label}")
        return 1

    print(f"PASS: plan names all {total}/{total} required symbols.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
