"""WFLOW-400 Task 6 (SOLUTION): child workflow vs activity + error handling.

Pick the right composition primitive (sub_workflows.md):

  - Use a CHILD WORKFLOW when the sub-process is itself long-running, needs its OWN retries and
    event history you can replay independently, or must be signalable/queryable from outside.
  - Use an ACTIVITY for a single side effect (one DB write, one API call) retried as a unit.

Here `enrich-record` is a durable sub-process with its own history -> child workflow.
`notify` is a single fire-and-forget side effect -> activity. The parent wraps child execution
so a child failure (WorkflowError) is handled rather than crashing the whole batch.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow


class EnrichInput(BaseModel):
    record_id: str


@workflows.activity()
async def notify(record_id: str) -> str:
    """Single side effect -> activity."""
    return f"notified:{record_id}"


@workflows.workflow.define(name="enrich-record")
class EnrichRecord:
    """Long-running sub-process with its own durable history -> child workflow."""

    @workflows.workflow.entrypoint
    async def run(self, params: EnrichInput) -> str:
        return f"enriched:{params.record_id}"


class BatchInput(BaseModel):
    record_ids: list[str]


@workflows.workflow.define(name="batch-orchestrator")
class BatchOrchestrator:
    @workflows.workflow.entrypoint
    async def run(self, params: BatchInput) -> list[str]:
        results: list[str] = []
        for record_id in params.record_ids:
            try:
                child_result = await workflows.execute_workflow(
                    EnrichRecord, params=EnrichInput(record_id=record_id)
                )
                results.append(child_result)
                await notify(record_id)
            except workflows.WorkflowError as exc:
                # A child failure is isolated; the batch keeps going.
                results.append(f"failed:{record_id}:{exc}")
        return results
