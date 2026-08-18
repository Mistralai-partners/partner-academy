"""WFLOW-TSE1 demo (STARTER): complete the durable invoice demo.

Right now this workflow does not tell the durable-execution story. It runs the PDF fetch INLINE in
the workflow body and mints its id with a raw uuid. That defeats the two things a customer cares
about most: an inline side effect is not a retry boundary, and a raw uuid in the workflow body
breaks deterministic replay after a restart. It also exposes no way to watch progress.

Your job (see tasks.md, T1 and T2):

- T1: fix the two anti-patterns so the demo tells the durability story — the side effect must sit
  at the retry boundary rather than inline in the body, and the id must come from an API that is
  safe across replay. Decide which construct holds each; tasks.md T1 names the docs.
- T2: expose a get_status query (read-only progress) and an approve signal (human approval) so the
  customer can watch and interact during the demo.

Grounded in the pinned Workflows docs (SHA a3e0f0c...): building-workflows/workflows.md,
building-workflows/activities/basics.md, building-workflows/workflows/determinism.md,
interacting-with-workflows/queries.md, interacting-with-workflows/signals.md.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow  # noqa: F401  (T1 needs a replay-safe id source from here)


class Invoice(BaseModel):
    invoice_id: str
    amount: float


class Status(BaseModel):
    stage: str
    approved: bool


# TODO T1: the PDF fetch below is a side effect (an HTTP download) run inline in the workflow body,
# so it is not on the retry boundary and the body cannot replay cleanly. Move it to where side
# effects belong and define that construct here. (tasks.md T1 hint; building-workflows docs.)


@workflows.workflow.define(
    name="invoice-demo",
    workflow_display_name="Invoice Demo",
    workflow_description="Durable invoice pipeline for the customer demo.",
)
class InvoiceWorkflow:
    def __init__(self) -> None:
        self.stage = "received"
        self.approved = False

    # TODO T2: add a get_status query (read-only progress) and an approve signal (human approval).

    @workflows.workflow.entrypoint
    async def run(self, invoice: Invoice) -> dict:
        # Inline side effect + non-deterministic id: this is the anti-pattern to fix in T1.
        trace_id = str(uuid.uuid4())
        pdf = f"pdf-bytes-for-{invoice.invoice_id}"  # a side effect run inline in the body (see TODO T1)
        return {"trace_id": trace_id, "invoice_id": invoice.invoice_id, "pdf": pdf}
