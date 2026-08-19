"""WFLOW-WS1 A2 - resilient_confirm (SOLUTION).

Drop this file into a scaffold created with:
 uvx mistralai-workflows-cli@latest setup

Scenario: the order confirmation step calls a flaky downstream service that
intermittently errors and intermittently wedges. This version adds the
durability configuration and heartbeats that let the execution self-heal.

What was added versus the starter, and why:
 * start_to_close_timeout: an outer bound so a single attempt can never run
 forever. It caps the blast radius of a truly stuck attempt.
 * retry_policy_max_attempts: enough attempts to clear the transient failures
 AND the one wedged attempt, plus a little headroom. The fault needs
 FAULT_FAILS_FIRST failures + 1 wedge + 1 success, so max_attempts is set
 above that count. Set deliberately, not by copying a default.
 * retry_policy_backoff_coefficient: 2.0 doubles the delay between attempts
 (1s, 2s, 4s, 8s), giving a transient fault time to clear without hammering
 the downstream.
 * heartbeat_timeout: much shorter than the wedge. Because the wedged attempt
 sends no heartbeat, the worker declares it dead within the heartbeat window
 and reschedules it in seconds, instead of waiting out the full
 start_to_close_timeout.
 * activity.heartbeat in the loop: the healthy path proves liveness every
 iteration. Without it, a healthy-but-slow loop would also trip the
 heartbeat_timeout, so the heartbeat is a required part of the fix, not a
 nicety.

The fault injector is unchanged from the starter.
"""

from __future__ import annotations

import asyncio
import os
import tempfile

from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
# Liveness API: the heartbeat is the top-level workflows.activity_heartbeat(...) (sync); there is no activity.heartbeat(...).
from mistralai.workflows import activity


WORKFLOW_NAME = "resilient_confirm"


# --- Input / output models -------------------------------------------------

class ConfirmRequest(BaseModel):
    order_id: str
    # A fresh request_id per run so the injected fault re-arms each execution.
    request_id: str


class ConfirmResult(BaseModel):
    order_id: str
    confirmation: str
    attempts_used: int


# --- PROVIDED fault injector (DO NOT REMOVE) -------------------------------
# Identical to the starter. See the starter file for the full explanation.

FAULT_FAILS_FIRST = 2 # attempts 1..2 raise a transient error
FAULT_HANG_SECONDS = 60 # the attempt after that wedges for this long


def _attempt_state_path(request_id: str) -> str:
    safe = "".join(c for c in request_id if c.isalnum() or c in ("-", "_"))
    return os.path.join(tempfile.gettempdir(), f"wflow_ws1_a2_attempt_{safe}.txt")


def _record_attempt(request_id: str) -> int:
    """Increment and return this execution's attempt number (persists across retries)."""
    path = _attempt_state_path(request_id)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            n = int(fh.read().strip() or "0")
    except (FileNotFoundError, ValueError):
        n = 0
    n += 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(str(n))
    return n


class TransientDownstreamError(Exception):
    """Raised by the fault injector to simulate a retryable downstream failure."""


async def _flaky_downstream_confirm(request_id: str) -> int:
    """Provided fault injector. Returns the attempt number when it finally succeeds."""
    attempt = _record_attempt(request_id)
    if attempt <= FAULT_FAILS_FIRST:
        raise TransientDownstreamError(
            f"downstream confirmation service errored (attempt {attempt})"
        )
    if attempt == FAULT_FAILS_FIRST + 1:
        # The service accepted the call and then wedged. It never returns on
        # its own, so heartbeat_timeout is what notices and gives up.
        await asyncio.sleep(FAULT_HANG_SECONDS)
    return attempt


# --- Activity --------------------------------------------------------------
@workflows.activity(
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=5,
    retry_policy_backoff_coefficient=2.0,
    heartbeat_timeout=timedelta(seconds=10),
)
async def confirm_order(request: ConfirmRequest) -> ConfirmResult:
    # Call the flaky downstream service (the injected fault lives in here).
    attempt = await _flaky_downstream_confirm(request.request_id)

    # Long confirmation loop: post the confirmation in steps, and prove liveness
    # on every step so the worker never mistakes a slow-but-healthy loop for a
    # wedged one.
    steps = 12
    for i in range(steps):
        await asyncio.sleep(1)
        workflows.activity_heartbeat({"processed": i + 1, "total": steps})

    # Idempotent side effect: the confirmation is derived only from order_id, so
    # a retry is safe to repeat and converges to the same observable state.
    confirmation = f"CONFIRMED:{request.order_id}"
    return ConfirmResult(
        order_id=request.order_id,
        confirmation=confirmation,
        attempts_used=attempt,
    )


# --- Workflow --------------------------------------------------------------

@workflows.workflow.define(name=WORKFLOW_NAME)
class ResilientConfirmWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: ConfirmRequest) -> ConfirmResult:
        # Activities are awaited directly.
        return await confirm_order(input)
