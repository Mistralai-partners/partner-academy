"""WFLOW-WS1 A2 - resilient_confirm (STARTER).

Drop this file into a scaffold created with:
 uvx mistralai-workflows-cli@latest setup

The worker auto-discovers workflows under src/workflows/, so no manual
registration is needed. See TASKS.md for the guided build.

Scenario: the order confirmation step now calls a flaky downstream service.
The service intermittently errors and intermittently wedges. In production the
execution must self-heal instead of dying or hanging. Your job is to add the
durability configuration that lets it recover. You do NOT change the fault
injector, and you do NOT change the workflow logic.
"""

from __future__ import annotations

import asyncio
import os
import tempfile

from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
# `activity` is imported for you: the liveness fix uses activity.heartbeat(...).
# [VERIFY] shipped WFLOW course material also shows a standalone activity_heartbeat(...) alias; context7 live docs use activity.heartbeat(...)
from mistralai.workflows import activity # noqa: F401 (used once you add heartbeats)


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
# This simulates a flaky downstream confirmation service. It is the scenario,
# not a bug to delete. It does two things across attempts:
# 1. the first few attempts raise a transient error (the service is erroring),
# 2. the next attempt accepts the call and then wedges: it sleeps far longer
# than any naive timeout (the service is hung and will never respond),
# 3. only a later attempt succeeds.
#
# Attempt state is kept on disk keyed by request_id. That is deliberate: a
# retry may re-enter in the same or a fresh worker process, and the fault must
# ADVANCE across retries instead of resetting to attempt 1. Reset-on-retry
# would make the fault un-survivable and the scenario meaningless.

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
        # its own, so something outside the activity has to notice and give up.
        await asyncio.sleep(FAULT_HANG_SECONDS)
    return attempt


# --- Activity --------------------------------------------------------------
# TODO: this activity has no durability config, so a transient failure kills the execution
@workflows.activity
async def confirm_order(request: ConfirmRequest) -> ConfirmResult:
    # Call the flaky downstream service (the injected fault lives in here).
    attempt = await _flaky_downstream_confirm(request.request_id)

    # Long confirmation loop: the confirmation is posted in steps. This runs
    # long enough that, from the worker's point of view, a silent activity is
    # indistinguishable from a dead one.
    steps = 12
    for _ in range(steps):
        await asyncio.sleep(1)
        # TODO: while this loop runs, nothing signals that the activity is still alive

    # Idempotent side effect: the confirmation is derived only from order_id, so
    # repeating this activity converges to the same observable state. Keeping it
    # idempotent is what makes a retry safe to repeat.
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
