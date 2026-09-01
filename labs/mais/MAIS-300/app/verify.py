#!/usr/bin/env python3
"""Acceptance check for the MAIS-300 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Runs the offline, deterministic test suite against the mais/ package. The tests
exercise every fixed bug (streaming fold, retry policy, RAG chunking, cosine
ranking, restart entry, embedding cost) using the real mistralai SDK types but
no network. Prints RESULT: PASS and exits 0 only when every check holds.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    print("== Verifying MAIS-300 lab ==")

    uv = shutil.which("uv")
    if uv:
        cmd = [
            uv, "run", "--no-project",
            "--with", "mistralai==2.9.4", "--with", "pytest",
            "python", "-m", "pytest", "tests", "-q",
        ]
    else:
        cmd = [sys.executable, "-m", "pytest", "tests", "-q"]

    result = subprocess.run(
        cmd,
        cwd=HERE,
        env={**os.environ, "PYTHONPATH": HERE},
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
