"""WFLOW-300 Task 1 (SOLUTION): idempotency under retry.

An activity is the retry boundary. When a charge activity times out mid-run, the platform
retries it with the SAME inputs. If the "did I already charge this?" key is minted inside
the activity (a fresh uuid on every attempt), each retry looks like a new logical charge and
the customer is billed twice.

The fix is to derive a STABLE idempotency key in the workflow body with the deterministic
`workflow.uuid4()` (stable across both replay and activity retries) and pass it into the
activity, which dedupes on it. A retry then carries the same key and becomes a no-op.

Grounded in: building-workflows/activities/basics.md (retries, granularity, "each one
idempotent and retried independently"), building-workflows/workflows/determinism.md
(workflow.uuid4 is the deterministic id source).
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow

# Stands in for the payment processor's idempotency store (the real store lives at your PSP).
# The lab's live check inspects it to prove a retried charge does not bill twice.
_LEDGER: dict[str, float] = {}


@workflows.activity()
async def charge_customer(idempotency_key: str, customer_id: str, amount: float) -> str:
    """Charge once per idempotency key. A retry carries the same key -> no double charge."""
    if idempotency_key in _LEDGER:
        return f"noop:{idempotency_key}"
    _LEDGER[idempotency_key] = amount
    return f"charged:{idempotency_key}"


class ChargeRequest(BaseModel):
    customer_id: str
    amount: float


@workflows.workflow.define(name="billing-workflow")
class BillingWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ChargeRequest) -> str:
        # Generate the key ONCE, deterministically. It is stable across replay and across
        # activity retries, so a retried charge dedupes correctly.
        idempotency_key = workflow.uuid4()
        return await charge_customer(str(idempotency_key), req.customer_id, req.amount)
