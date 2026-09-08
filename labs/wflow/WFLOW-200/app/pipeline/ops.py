"""WFLOW-200 Task 12 (SOLUTION): run in a deployment, read a trace, raise a typed error.

Three everyday production concerns:

- **Deployments.** A worker registers its workflows under a `DEPLOYMENT_NAME`. If two deployments
  register the SAME workflow name, executions route by deployment, so a name collision across
  deployments sends work to the wrong worker. Keep the name unique per logical deployment.
- **Observability.** Every execution emits an OpenTelemetry (OTel) trace: one span per workflow and
  activity, with timings and status. You read that trace summary to see where a run spent its time
  and which activity failed, instead of guessing from logs.
- **Error handling.** For an EXPECTED failure (a validation problem, a known bad input), raise a
  `WorkflowsException` with a structured `ErrorCode` instead of a bare `Exception`. The platform
  surfaces the code so callers can branch on it, and terminal codes (the `WF_XXXX` catalog, e.g.
  `WF_1104` = workflow registration not authorized) tell you the run will not recover.

Executable boundary (honest): `DEPLOYMENT_NAME` routing and the live OTel trace need a running
worker + platform, so they are documented and referenced, not run offline. Raising and inspecting
a `WorkflowsException` (its `.code`, `.is_terminal()`) is real SDK behavior and runs live here.

Grounded in: installed mistralai-workflows==3.10.0 — `WorkflowsException(message, code=ErrorCode)`
with `.code` / `.is_terminal()` / terminal `WF_` codes (exceptions.py); `DEPLOYMENT_NAME` worker
config (core/config/config.py); OTel spans (core config `otel_enabled`).
"""
from __future__ import annotations

import mistralai.workflows as workflows
from mistralai.workflows.exceptions import ErrorCode, WorkflowsException

# The worker reads DEPLOYMENT_NAME from its environment at startup. Two deployments that register
# the same workflow name are distinguished by this value; a collision routes work to the wrong one.
DEPLOYMENT_NAME_ENV = "DEPLOYMENT_NAME"


@workflows.activity()
async def charge_account(account_id: str, cents: int) -> dict:
    """Raise a TYPED, structured error for an expected bad input instead of a bare Exception,
    so the caller can branch on the code and the platform can classify it."""
    if cents <= 0:
        raise WorkflowsException(
            message=f"charge amount must be positive, got {cents}",
            code=ErrorCode.INVALID_ARGUMENTS_ERROR,
        )
    return {"account_id": account_id, "charged": cents}


def is_recoverable(exc: WorkflowsException) -> bool:
    """Read a raised WorkflowsException: a terminal WF_XXXX-coded error will not recover;
    a transient one is safe to retry. This is the everyday triage a code lets you do."""
    return not exc.is_terminal()


@workflows.workflow.define(name="billing-ops-workflow")
class BillingOpsWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, account_id: str, cents: int) -> dict:
        return await charge_account(account_id, cents)
