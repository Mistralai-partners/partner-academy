"""WFLOW-300 Task 7 (SOLUTION): configure an activity, then keep it idempotent under retry.

Two failures hide behind one activity. First, an unconfigured activity blocks forever on a
stalled call, never retries a transient failure, and gives the platform no way to notice a
long call has gone silent. Second, once retries ARE on, the activity becomes the retry
boundary: the platform re-runs it with the SAME inputs, so any side effect that isn't keyed
on a stable id happens twice.

The fix is both halves together:
  - Configure the decorator: `start_to_close_timeout` caps a single attempt;
    `retry_policy_max_attempts` + `retry_policy_backoff_coefficient` retry transients with
    exponential backoff; `heartbeat_timeout` plus periodic `activity_heartbeat()` on a long
    call let the platform fail-fast a stall instead of waiting out the whole timeout.
  - Derive the idempotency key ONCE in the workflow body with the deterministic
    `workflow.uuid4()` (stable across replay AND across activity retries) and pass it in. A
    retried charge then carries the same key and dedupes to a no-op.

Grounded in: building-workflows/activities/basics.md (Timeouts / Retry policies / Heartbeat,
"each one idempotent and retried independently"), building-workflows/workflows/determinism.md
(workflow.uuid4 is the deterministic id source).
"""
from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow

# Stands in for the payment processor's idempotency store (the real store lives at your PSP).
# The lab's live check inspects it to prove a retried charge does not bill twice.
_LEDGER: dict[str, float] = {}


@workflows.activity(
    name="charge-customer",
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=5,
    retry_policy_backoff_coefficient=2.0,
    heartbeat_timeout=timedelta(seconds=15),
)
async def charge_customer(idempotency_key: str, customer_id: str, amount: float) -> str:
    """Charge once per idempotency key. A retry carries the same key -> no double charge.

    The timeout caps a single attempt, retries cover a transient PSP failure, and the key
    makes each retry safe."""
    if idempotency_key in _LEDGER:
        return f"noop:{idempotency_key}"
    _LEDGER[idempotency_key] = amount
    return f"charged:{idempotency_key}"


@workflows.activity(
    name="reconcile-ledger",
    start_to_close_timeout=timedelta(minutes=10),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
    heartbeat_timeout=timedelta(seconds=30),
)
async def reconcile_ledger(day: str, n_pages: int) -> dict:
    """A long reconciliation call. It heartbeats each page so the platform can detect a stall
    within `heartbeat_timeout` instead of waiting out the full `start_to_close_timeout`."""
    reconciled = 0
    for page in range(n_pages):
        # Emit progress so a stalled attempt fails fast; heartbeat payload is the resume point.
        workflows.activity_heartbeat({"day": day, "page": page})
        reconciled += 1
    return {"day": day, "reconciled": reconciled}


class ChargeRequest(BaseModel):
    customer_id: str
    amount: float


@workflows.workflow.define(name="billing-config-workflow")
class BillingConfigWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ChargeRequest) -> str:
        # Mint the key ONCE, deterministically. It is stable across replay and across activity
        # retries, so a retried charge dedupes correctly.
        idempotency_key = workflow.uuid4()
        return await charge_customer(str(idempotency_key), req.customer_id, req.amount)
