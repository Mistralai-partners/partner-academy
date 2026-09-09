"""WFLOW-400 Task 2 (L1.2): enforce determinism and rank the fixes.

A workflow body is replayed from its event history after any worker restart. Any value that
differs between the first run and the replay (wall-clock time, a fresh uuid, a random draw, a file
read) makes replay diverge and the execution fails a non-determinism check. That is why the code
"works locally" and only breaks after a restart.

The fixes have a precedence order, and choosing the right one is the L400 skill:

  1. Prefer a deterministic workflow API. `workflow.now()`, `workflow.uuid4()`, `workflow.random()`
     replay to the SAME value from history. This is the first choice for a time/uuid/random value.
  2. Move the side effect into an `@activity`. Activities are not replayed, so real I/O
     (network, file, db) belongs there, never in the body.
  3. Only then reach for an escape hatch. `workflow.unsafe.imports_passed_through()` lets a library
     with import-time side effects through the sandbox; `skip_determinism_enforcement()` exists for
     a one-off you have proven safe. An escape hatch is the last resort, not the fix.

Executable boundary (honest): the good body (`StampWorkflow`) is linted to zero violations by the
AST determinism linter and registers via the real SDK with enforcement on. The bundled
anti-pattern (`pipeline/determinism_antipattern.py`) is the same lint run over a body that DOES
call banned APIs, so the linter must flag it (>0). Real replay needs the orchestrator.

Grounded in: building-workflows/workflows/determinism.md; the shipped detlint.py banned-call list;
WFLOW-200 determinism.py (`workflow.now`/`uuid4`/`random` + `imports_passed_through`).
"""
from __future__ import annotations

import mistralai.workflows as workflows
from mistralai.workflows import workflow

# Fix 3 (escape hatch): import a library through the sandbox untouched. Shown with a stdlib module
# for a runnable example; in production this guards a C-extension or a client with import-time
# side effects (the same hatch the shipped processor.py uses for the encryption import).
with workflow.unsafe.imports_passed_through():
    import math


@workflows.activity()
async def load_reference(key: str) -> float:
    """Fix 2: real I/O lives in an activity, which is not replayed."""
    return float(len(key))


@workflows.workflow.define(name="stamp-workflow")
class StampWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, key: str) -> dict:
        # Fix 1: deterministic APIs only -> these replay to the SAME value from history.
        request_id = workflow.uuid4()
        started_at = workflow.now()
        jitter = workflow.random().random()
        reference = await load_reference(key)  # Fix 2: I/O in the activity, not the body
        return {
            "request_id": str(request_id),
            "started_at": started_at.isoformat(),
            "jitter": jitter,
            "reference": reference,
            "hatch": math.sqrt(reference),  # math imported via the sandbox hatch above
        }


# Precedence rank an operator can apply to a diagnosed non-determinism (1 = try first).
FIX_PRECEDENCE = {
    "deterministic_workflow_api": 1,  # workflow.now / uuid4 / random
    "move_to_activity": 2,            # push the side effect into an @activity
    "escape_hatch": 3,               # imports_passed_through / skip_determinism_enforcement
}


def preferred_fix(issue: str) -> str:
    """Map a diagnosed non-determinism to the first fix to try (offline, pure logic)."""
    time_uuid_random = {"datetime.now", "time.time", "uuid.uuid4", "random.random"}
    io_calls = {"open", "requests.get", "httpx.get", "os.listdir"}
    if issue in time_uuid_random:
        return "deterministic_workflow_api"
    if issue in io_calls:
        return "move_to_activity"
    return "escape_hatch"
