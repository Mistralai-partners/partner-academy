"""WFLOW-400 Task 6 (L3.2): child workflow vs activity + typed error classification.

Pick the right composition primitive (sub_workflows.md):

  - Use a CHILD WORKFLOW when the sub-process is itself long-running, needs its OWN retries and
    event history you can replay independently, or must be signalable/queryable from outside.
  - Use an ACTIVITY for a single side effect (one DB write, one API call) retried as a unit.

Here `enrich-record` is a durable sub-process with its own history -> child workflow.
`notify` is a single fire-and-forget side effect -> activity. The parent wraps child execution
so a child failure (`WorkflowError`) is isolated rather than crashing the whole batch.

The L400 add is error triage. When an activity raises a typed `WorkflowsException` with a
structured `ErrorCode`, the parent must classify it: a TERMINAL code (`is_terminal()` -> the
`WF_XXXX` catalog, e.g. registration-not-authorized) will not recover and should stop the run; a
transient one is safe to retry. `classify_error` below is that decision, and it runs live.
Continue-as-new (the third composition tool) is demonstrated in the shipped `processor.py`.

Grounded in: sub_workflows.md (`execute_workflow` / `WorkflowError`); WFLOW-200 ops.py
(`WorkflowsException` / `ErrorCode` / `is_terminal()`); processor.py (continue-as-new carry-forward).
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from mistralai.workflows.exceptions import ErrorCode, WorkflowsException


def classify_error(exc: WorkflowsException) -> dict:
    """Triage a raised WorkflowsException (offline, live SDK logic).

    A terminal WF_XXXX-coded error will not recover -> stop and surface it. A non-terminal one is
    transient -> the platform's retry policy can recover it.
    """
    terminal = exc.is_terminal()
    return {
        "code": exc.code.value if exc.code else None,
        "terminal": terminal,
        "action": "stop_and_page" if terminal else "retry",
    }


class EnrichInput(BaseModel):
    record_id: str


@workflows.activity()
async def notify(record_id: str) -> str:
    """Single side effect -> activity."""
    return f"notified:{record_id}"


@workflows.activity()
async def enrich_or_raise(record_id: str) -> str:
    """Raise a TYPED, structured error for a known-bad input so the parent can classify it,
    instead of a bare Exception the platform cannot triage."""
    if not record_id:
        raise WorkflowsException(
            message="record_id must be non-empty",
            code=ErrorCode.INVALID_ARGUMENTS_ERROR,
        )
    return f"enriched:{record_id}"


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
