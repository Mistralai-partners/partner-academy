"""WFLOW-300 Task 3 (SOLUTION): root-cause post-restart non-determinism.

The workflow body is replayed from event history whenever a worker restarts or the
execution is recovered. Any value that differs between the first run and the replay
(wall-clock time, a fresh uuid, a random draw, an env var, a file read) produces a
different command stream and the workflow fails with a non-determinism error. This is
why it "works locally" and only breaks after a restart.

The fix: every non-deterministic value comes from a deterministic workflow API
(workflow.now / workflow.uuid4 / workflow.random), and every side effect (file/network/db)
moves into an @activity, which is NOT replayed.

Escape hatches (use sparingly, documented in tasks.md): `workflow.unsafe.imports_passed_through()`
for libraries with import-time side effects, and `workflow.unsafe.skip_determinism_enforcement()`
for a one-off you know is safe. The right answer here is an activity, not an escape hatch.

Grounded in: building-workflows/workflows/determinism.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows
from mistralai.workflows import workflow


@workflows.activity()
async def load_config(path: str) -> dict:
    # File / network / db I/O is safe here: activities are not replayed.
    with open(path) as fh:
        return {"raw": fh.read()}


@workflows.workflow.define(name="report-workflow")
class ReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, path: str) -> dict:
        # Deterministic APIs only: these replay to the SAME value from the event history.
        request_id = workflow.uuid4()
        started_at = workflow.now()
        jitter = workflow.random()
        cfg = await load_config(path)
        return {
            "request_id": str(request_id),
            "started_at": started_at.isoformat(),
            "jitter": jitter,
            "config_bytes": len(cfg["raw"]),
        }
