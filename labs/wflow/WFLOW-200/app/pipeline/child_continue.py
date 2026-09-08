"""WFLOW-200 Task 9 (SOLUTION): child workflows, continue-as-new, and a recurring schedule.

A long-running processor hits three everyday needs, each with one right primitive:

- A heavy per-item sub-process that wants its OWN durable history and retries is a **child
  workflow**, launched with `execute_workflow(Child, params=...)` — not an activity, and not
  inlined in the parent. A child failure surfaces as `WorkflowError`, which the parent catches so
  one bad record does not sink the batch.
- Event history grows with every child call, so a processor that runs for a long time must
  **reset history while staying alive**: it carries its progress forward in a small state model
  and calls `workflow.continue_as_new(state)`. In production the trigger is
  `workflow.should_continue_as_new()` (history-size aware); here we also continue while work
  remains so the carry-forward is easy to follow and test offline.
- To run it on a cadence, you register a **schedule** from the CLIENT with
  `client.workflows.schedules.schedule_workflow(schedule=ScheduleDefinition(...), ...)`. The old
  schedule decorator is deprecated and deliberately not used.

Executable boundary (honest): running the parent/child and creating the schedule need a live
worker + client, so those are shown and checked structurally. The carry-forward math
(`advance_window`) is pure and runs live, offline.

Grounded in: installed mistralai-workflows==3.10.0 — `execute_workflow` + `WorkflowError`,
`workflow.continue_as_new` / `workflow.should_continue_as_new` (core/workflow.py),
`ScheduleDefinition` / `SchedulePolicy` / `ScheduleOverlapPolicy` (models/schedule.py), client
`workflows.schedules.schedule_workflow`. Prior art: WFLOW-300 child_continue.py + scale.py.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from mistralai.workflows.models import (
    ScheduleDefinition,
    ScheduleOverlapPolicy,
    SchedulePolicy,
)


class EnrichParams(BaseModel):
    record_id: int


@workflows.workflow.define(name="enrich-step")
class EnrichStep:
    """The heavy per-item step. A child workflow because it wants its own retries and a history
    you can replay independently of the parent batch."""

    @workflows.workflow.entrypoint
    async def run(self, params: EnrichParams) -> int:
        return params.record_id * 2  # stand-in for a durable enrichment sub-process


class WindowState(BaseModel):
    """Carry-forward state: everything continue_as_new needs to resume after a history reset."""
    offset: int = 0
    total_processed: int = 0
    window_size: int = 5
    n_records: int = 20


def advance_window(state: WindowState, processed_in_window: int) -> WindowState:
    """Pure carry-forward math (offline-testable): fold one processed window into the next state."""
    return WindowState(
        offset=min(state.offset + state.window_size, state.n_records),
        total_processed=state.total_processed + processed_in_window,
        window_size=state.window_size,
        n_records=state.n_records,
    )


@workflows.workflow.define(name="windowed-processor")
class WindowedProcessor:
    @workflows.workflow.entrypoint
    async def run(self, state: WindowState) -> int:
        # Process one window, each record as an isolated CHILD workflow.
        end = min(state.offset + state.window_size, state.n_records)
        processed = 0
        for record_id in range(state.offset, end):
            try:
                await workflows.execute_workflow(
                    EnrichStep, params=EnrichParams(record_id=record_id)
                )
                processed += 1
            except workflows.WorkflowError:
                # A child failure is isolated; keep the batch alive.
                continue

        nxt = advance_window(state, processed)

        # Reset history while staying alive if work remains. In production, gate this on
        # workflow.should_continue_as_new() so the reset tracks real history size.
        if nxt.offset < nxt.n_records:
            workflow.continue_as_new(nxt)

        return nxt.total_processed


# ---- Scheduling: register a recurring run from the CLIENT (decorator is deprecated) ---
def build_processor_schedule() -> ScheduleDefinition:
    """A daily run at 02:00, overlap=SKIP so a slow run never builds a backlog."""
    return ScheduleDefinition(
        input={"offset": 0},
        cron_expressions=["0 2 * * *"],
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
    )


def schedule_processor(client: Any) -> Any:
    """Register the schedule on the platform via the CLIENT.

    `client` is an authenticated `mistralai.client.Mistral`. This call reaches the live platform
    (auth + a registered/deployed workflow), so it runs against a real deployment, not offline —
    the lab checks the schedule SHAPE (built above) and this call site structurally."""
    return client.workflows.schedules.schedule_workflow(
        schedule=build_processor_schedule(),
        workflow_identifier="windowed-processor",
    )
