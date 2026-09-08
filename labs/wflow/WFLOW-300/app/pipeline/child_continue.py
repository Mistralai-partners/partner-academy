"""WFLOW-300 Task 12 (SOLUTION): parent + child workflow, a wait gate, and continue-as-new.

A long batch coordinator hits three limits at once, and each has one right primitive:

- A heavy per-item sub-process that needs its OWN durable history and retries is a **child
  workflow**, launched with `execute_workflow(Child, params=...)` — not an activity, and not
  inlined in the parent. A child failure surfaces as `WorkflowError`, which the parent catches so
  one bad record does not sink the batch.
- The coordinator must **pause at zero cost** until an operator approves the next window. That is
  `workflow.wait_condition(predicate, timeout=...)` flipped by a signal (the approval pattern from
  approval.py), with a handled timeout so it can't hang forever.
- Event history grows with every child call, so the coordinator must **reset history while staying
  logically alive**: it carries its progress forward in a small state model and calls
  `workflow.continue_as_new(state)`. In production the trigger is
  `workflow.should_continue_as_new()` (history-size aware); here we also continue while work
  remains so the carry-forward is easy to follow and to test offline.

Grounded in: WFLOW-400 orchestrator.py (`execute_workflow` child call + `WorkflowError`),
WFLOW-400 processor.py (`should_continue_as_new` / `continue_as_new` carry-forward),
WFLOW-300 approval.py (`wait_condition` + signal + timeout). Continue-as-new takes a BaseModel:
confirmed via installed mistralai-workflows==3.10.0 (`workflow.continue_as_new(params: BaseModel)`).
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow


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
    def __init__(self) -> None:
        self.approved = False

    @workflows.workflow.signal(name="approve_window")
    async def approve_window(self) -> None:
        # External approval flips the gate the entrypoint is waiting on.
        self.approved = True

    @workflows.workflow.entrypoint
    async def run(self, state: WindowState) -> int:
        # Gate: suspend cheaply until this window is approved, but never hang forever.
        try:
            await workflow.wait_condition(lambda: self.approved, timeout=timedelta(hours=1))
        except asyncio.TimeoutError:
            return state.total_processed

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
