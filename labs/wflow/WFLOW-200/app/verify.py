#!/usr/bin/env python3
"""Acceptance check for the WFLOW-200 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Runs the structural acceptance checks against the pipeline/ package: SDK
registration, activity metadata, interaction primitives, agent wiring, and
payload offloading. Uses the REAL mistralai-workflows SDK but makes no network
calls. Prints RESULT: PASS and exits 0 only when every check holds.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    print("== Verifying WFLOW-200 lab ==")

    checks = os.path.join(HERE, "checks.py")
    if not os.path.exists(checks):
        print("  FAIL: checks.py is missing")
        print("RESULT: FAIL")
        sys.exit(1)

    uv = shutil.which("uv")
    if uv:
        cmd = [
            uv, "run", "--no-project",
            "--with", "mistralai-workflows[mistralai]==3.10.0",
            "python", checks, ".",
        ]
    else:
        cmd = [sys.executable, checks, "."]

    env = {**os.environ, "PYTHONPATH": HERE}
    result = subprocess.run(cmd, cwd=HERE, env=env)

    if result.returncode == 0:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
