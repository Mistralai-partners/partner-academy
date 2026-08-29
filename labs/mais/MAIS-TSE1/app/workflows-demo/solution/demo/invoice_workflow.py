"""WFLOW-TSE1 demo (SOLUTION): a durable invoice-processing workflow.

This is the happy-path demo a technical seller stands up in front of a customer. Everything a
prospect asks about the durable-execution story is visible in one small workflow:

- Durable orchestration. Every step is recorded in an event history; if a worker crashes, another
  resumes from the last completed step. Work is not lost.
- Hybrid execution. Mistral hosts the orchestrator; THIS worker code runs in the customer's own
  environment. Workers connect outbound; the orchestrator never opens a connection into their
  network.
- The activity boundary. The side effect (the PDF fetch over HTTP) lives in an @activity, which is
  the retry boundary. If the partner API blips, the platform retries just that step, not the whole
  run.
- Determinism. The workflow body derives its id from workflow.uuid4() (not uuid.uuid4()), so the
  body replays cleanly from history after a restart.
- Observable by default. A get_status query lets the customer watch progress live during the demo.
- Human-in-the-loop. The workflow can pause on an 'approve' signal for invoices that need review.

Grounded in the pinned Workflows docs (SHA a3e0f0c...): getting-started/overview.md,
building-workflows/workflows.md, building-workflows/activities/basics.md,
building-workflows/workflows/determinism.md, interacting-with-workflows/queries.md,
interacting-with-workflows/signals.md.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow


class Invoice(BaseModel):
    invoice_id: str
    amount: float


class Status(BaseModel):
    stage: str
    approved: bool


# The PDF fetch is a SIDE EFFECT (an HTTP download). Side effects belong in an @activity, never in
# the workflow body: the activity is the unit that is retried automatically and is never replayed.
@workflows.activity()
async def fetch_invoice_pdf(invoice_id: str) -> str:
    """Download the invoice PDF. In a live demo this is a real HTTP call to the partner API.

    The teaching point for the customer: this call is the retry boundary. A transient failure here
    is retried by the platform with configurable backoff, and the rest of the workflow is untouched.
    """
    return f"pdf-bytes-for-{invoice_id}"


@workflows.workflow.define(
    name="invoice-demo",
    workflow_display_name="Invoice Demo",
    workflow_description="Durable invoice pipeline for the customer demo.",
)
class InvoiceWorkflow:
    def __init__(self) -> None:
        self.stage = "received"
        self.approved = False

    @workflows.workflow.query(name="get_status", description="Live progress for the demo.")
    def get_status(self) -> Status:
        # A query is read-only: it exposes state to external callers without modifying the run.
        return Status(stage=self.stage, approved=self.approved)

    @workflows.workflow.signal(name="approve", description="Reviewer approves the invoice.")
    async def approve(self, invoice: Invoice) -> None:
        # A signal is fire-and-forget: an external reviewer nudges the workflow; it updates state.
        self.approved = True

    @workflows.workflow.entrypoint
    async def run(self, invoice: Invoice) -> dict:
        # A deterministic id from the workflow API. Safe across replay (not the stdlib uuid module).
        trace_id = str(workflow.uuid4())
        self.stage = "fetching"
        pdf = await fetch_invoice_pdf(invoice.invoice_id)
        self.stage = "done"
        return {"trace_id": trace_id, "invoice_id": invoice.invoice_id, "pdf": pdf}
