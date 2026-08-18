"""WFLOW-300 Task 3 (STARTER): a workflow that breaks only after a restart.

SYMPTOM: this workflow passes every local run, then fails in production with a
non-determinism error after a worker restart or recovery. The failure never reproduces
on a clean first run.

Diagnose every value in the workflow body that would differ between the first run and a
replay from event history, and every side effect that must not live in the body. Reference:
../../solution/pipeline/determinism.py, building-workflows/workflows/determinism.md
(including the escape hatches under workflow.unsafe).
"""
from __future__ import annotations

import datetime
import os
import random
import uuid

import mistralai.workflows as workflows


@workflows.workflow.define(name="report-workflow")
class ReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, path: str) -> dict:
        # SYMPTOM: each of these produces a different value on replay than on the first run.
        request_id = uuid.uuid4()
        started_at = datetime.datetime.now()
        jitter = random.random()
        region = os.environ.get("REGION", "us")
        # SYMPTOM: direct I/O in the workflow body is re-executed on every replay.
        with open(path) as fh:
            raw = fh.read()
        return {
            "request_id": str(request_id),
            "started_at": started_at.isoformat(),
            "jitter": jitter,
            "region": region,
            "config_bytes": len(raw),
        }
