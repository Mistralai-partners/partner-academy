"""WFLOW-200 Task 7 (SOLUTION): keep the workflow body deterministic.

The workflow body is replayed from event history whenever a worker restarts. Any value that
differs between the first run and the replay (wall-clock time, a fresh uuid, a random draw, a
file read) produces a different command stream and the workflow fails with a non-determinism
error. That is why it "works locally" and only breaks after a restart.

The everyday fix has two halves:

- Every non-deterministic value comes from a deterministic workflow API: `workflow.now()`,
  `workflow.uuid4()`, `workflow.random()`. These replay to the SAME value from history.
- Every side effect (file, network, db) moves into an `@activity`, which is NOT replayed.

When a library genuinely must be imported despite import-time side effects, the escape hatch is
`workflow.unsafe.imports_passed_through()` (shown below). The related body-level hatch,
`workflow.unsafe.skip_determinism_enforcement()`, exists for a one-off you know is safe; reach for
an activity first, and an escape hatch only when there is no alternative.

Grounded in: building-workflows/workflows/determinism.md; installed mistralai-workflows==3.10.0
(`workflow.now` / `workflow.uuid4` / `workflow.random` in core/workflow.py;
`workflow.unsafe.imports_passed_through()` used in WFLOW-300 payload_codec.py).
"""
from __future__ import annotations

import mistralai.workflows as workflows
from mistralai.workflows import workflow

# Escape hatch: import a library through the sandbox untouched. Shown here with a stdlib module
# for a runnable example; in production this guards a C-extension or a client with import-time
# side effects (the same hatch WFLOW-300 payload_codec.py uses for `cryptography`).
with workflow.unsafe.imports_passed_through():
    import math


@workflows.activity()
async def fetch_exchange_rate(pair: str) -> float:
    # Network I/O is safe here: activities are not replayed. A real call would hit an FX API.
    return 1.25 if pair == "GBPUSD" else 1.0


@workflows.workflow.define(name="fx-report-workflow")
class FxReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, pair: str) -> dict:
        # Deterministic APIs only: these replay to the SAME value from the event history.
        request_id = workflow.uuid4()
        started_at = workflow.now()
        jitter = workflow.random().random()
        rate = await fetch_exchange_rate(pair)  # I/O lives in the activity, not the body
        return {
            "request_id": str(request_id),
            "started_at": started_at.isoformat(),
            "jitter": jitter,
            "pair": pair,
            "rate": rate,
        }


@workflows.workflow.define(name="escape-hatch-workflow")
class EscapeHatchWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, x: float) -> dict:
        # `math` was imported through workflow.unsafe.imports_passed_through() above, so the
        # determinism sandbox lets it through. math.sqrt is pure, so this stays deterministic.
        return {"sqrt": math.sqrt(x)}
