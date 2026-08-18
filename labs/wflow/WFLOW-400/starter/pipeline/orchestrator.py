"""WFLOW-400 Task 6 (STARTER): wrong composition primitive.

`enrich-record` is a long-running, independently-durable sub-process that should be a CHILD
WORKFLOW, but here it is modeled as an activity. That gives it no independent history, no
independent retries, and nothing you can signal or query from outside.

Fix: extract the enrichment into its own `@workflows.workflow.define(name="enrich-record")`
child workflow and call it from the parent with `workflows.execute_workflow(...)`, handling a
child `WorkflowError` so one bad record does not sink the batch. Keep `notify` as an activity.

Reference: ../../solution/pipeline/orchestrator.py, sub_workflows.md.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows


class EnrichInput(BaseModel):
    record_id: str


@workflows.activity()
async def notify(record_id: str) -> str:
    return f"notified:{record_id}"


# BUG (Task 6): a durable, long-running sub-process modeled as an activity instead of a child workflow.
@workflows.activity()
async def enrich_record(record_id: str) -> str:
    return f"enriched:{record_id}"


class BatchInput(BaseModel):
    record_ids: list[str]


@workflows.workflow.define(name="batch-orchestrator")
class BatchOrchestrator:
    @workflows.workflow.entrypoint
    async def run(self, params: BatchInput) -> list[str]:
        results: list[str] = []
        for record_id in params.record_ids:
            results.append(await enrich_record(record_id))   # BUG: should be a child workflow
            await notify(record_id)
        return results
