"""WFLOW-300 Task 1 (STARTER): idempotency under retry.

SYMPTOM: a charge activity occasionally times out mid-run and is retried. Customers are
sometimes billed twice. The ledger below ends up with TWO entries for a single logical
charge whenever the activity runs more than once.

Diagnose why a retried activity produces a second charge, then make a retry of the SAME
logical charge a no-op. Reference: ../../solution/pipeline/billing.py,
building-workflows/activities/basics.md, building-workflows/workflows/determinism.md.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel

import mistralai.workflows as workflows

# Stands in for the payment processor's idempotency store.
_LEDGER: dict[str, float] = {}


@workflows.activity()
async def charge_customer(customer_id: str, amount: float) -> str:
    # SYMPTOM: retrying this activity with identical inputs records a second charge.
    key = str(uuid.uuid4())
    _LEDGER[key] = amount
    return f"charged:{key}"


class ChargeRequest(BaseModel):
    customer_id: str
    amount: float


@workflows.workflow.define(name="billing-workflow")
class BillingWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ChargeRequest) -> str:
        return await charge_customer(req.customer_id, req.amount)
