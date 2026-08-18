"""WFLOW-300 Task 2 (STARTER): a human-in-the-loop approval that misbehaves.

SYMPTOMS, all at once:
  - This workflow pins a CPU while it waits.
  - Approvals sent to it from outside are silently dropped (nothing ever flips).
  - If approval never arrives, the execution hangs forever.

Diagnose which primitive each symptom needs, then make the approval suspend at no cost,
receive its approval from outside, and give up after a bounded wait. Reference:
../../solution/pipeline/approval.py, interacting-with-workflows/signals.md,
building-workflows/waiting_for_conditions.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.workflow.define(name="approval-workflow")
class ApprovalWorkflow:
    def __init__(self) -> None:
        self.approved = False

    # SYMPTOM: external approvals never reach the running workflow.
    async def approve(self) -> None:
        self.approved = True

    @workflows.workflow.entrypoint
    async def run(self, request_id: str) -> str:
        # SYMPTOM: busy-wait that pins a CPU and, with no upper bound, blocks forever.
        while not self.approved:
            pass
        return f"approved:{request_id}"
