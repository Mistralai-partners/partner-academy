#!/usr/bin/env python3
"""WFLOW-300 walkthrough verifier.

Run from inside app/:
    python3 verify.py

Uses uv to fetch the pinned SDK, then delegates to checks.py (which also
imports detlint.py from the same directory).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

uv = shutil.which("uv")
if not uv:
    print("FAIL: uv is not installed. Install from https://docs.astral.sh/uv/")
    sys.exit(1)

checks = os.path.join(HERE, "checks.py")
result = subprocess.run(
    [uv, "run", "--no-project",
     "--with", "mistralai-workflows[mistralai]==3.10.0",
     "python", checks, "."],
    cwd=HERE,
)
sys.exit(result.returncode)
