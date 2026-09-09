"""WFLOW-400 Task 2 fixture: an intentional non-determinism ANTI-PATTERN.

This module exists ONLY as a target for the determinism linter (detlint.py). checks.py never
imports it — it passes this file's PATH to `detlint.lint_entrypoints`, which AST-parses it and
must report >0 violations. Do NOT copy this into a real workflow; every call in `run` below is a
banned non-deterministic call that would fail replay after a worker restart.

The correct version is `pipeline/determinism.py` (`StampWorkflow`), which lints to zero.
"""
from __future__ import annotations

import datetime
import random

import mistralai.workflows as workflows


@workflows.workflow.define(name="bad-stamp-workflow")
class BadStampWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, path: str) -> dict:
        # Every one of these is banned in a workflow body: wall-clock time, a fresh uuid-equivalent
        # random draw, and direct file I/O. They diverge on replay and fail the determinism check.
        stamped_at = datetime.datetime.now()          # banned: datetime.now
        draw = random.random()                        # banned: random.random
        with open(path) as fh:                        # banned: open() + file I/O in the body
            first_line = fh.readline()
        return {"stamped_at": stamped_at.isoformat(), "draw": draw, "first_line": first_line}
