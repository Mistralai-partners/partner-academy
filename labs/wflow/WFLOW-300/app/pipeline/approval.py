"""WFLOW-300 Task 2 (SOLUTION): wait_condition + signal + timeout, all three at once.

A human-in-the-loop approval must satisfy three constraints simultaneously:
  1. It must SUSPEND at no compute cost until approved (not busy-wait / pin a CPU).
  2. It must be able to RECEIVE the approval from outside (a declared signal handler).
  3. It must not hang forever if approval never comes (a timeout with a handled expiry).

`workflow.wait_condition(predicate, timeout=...)` covers 1 and 3; a `@workflow.signal`
handler flips the predicate for 2. On expiry, `wait_condition` raises `asyncio.TimeoutError`.

Grounded in: interacting-with-workflows/signals.md, building-workflows/waiting_for_conditions.md.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

import mistralai.workflows as workflows
from mistralai.workflows import workflow


@workflows.workflow.define(name="approval-workflow")
class ApprovalWorkflow:
    def __init__(self) -> None:
        self.approved = False

    @workflows.workflow.signal(name="approve")
    async def approve(self) -> None:
        # Asynchronous signal from outside flips the predicate wait_condition is watching.
        self.approved = True

    @workflows.workflow.entrypoint
    async def run(self, request_id: str) -> str:
        try:
            # Suspends at zero compute cost until `approved` is True or the timeout fires.
            await workflow.wait_condition(
                lambda: self.approved,
                timeout=timedelta(hours=24),
            )
        except asyncio.TimeoutError:
            return f"expired:{request_id}"
        return f"approved:{request_id}"
