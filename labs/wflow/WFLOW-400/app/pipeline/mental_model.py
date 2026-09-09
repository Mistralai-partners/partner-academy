"""WFLOW-400 Task 1 (L1.1): the execution mental model + the history-cap decision.

Four nouns carry the whole model. A **worker** is your process running your `@workflow.define`
and `@activity` code. A **deployment** is a named group of workers that share a task queue; the
platform routes an execution to the deployment that registered its workflow name. An **execution**
is one running instance of a workflow. Its durable memory is an ordered **event** history that the
orchestrator replays to rebuild state after any restart.

The L400 decision this module makes real: that history is capped (~51,200 events / ~50MB). A
long-running loop that never resets its history will hit the cap and fail. `continue_as_new`
resets the history while carrying state forward, so the skill is estimating the cadence: how many
loop iterations fit under the cap, and at what iteration count you should reset with a safety
margin instead of waiting for the hard ceiling.

Executable boundary (honest): the cap arithmetic is pure logic and runs live here. The minimal
`HeartbeatEcho` workflow anchors the worker/deployment/execution/event vocabulary and is checked
STRUCTURALLY (it registers via the real SDK); replaying an execution needs the orchestrator.

Grounded in: getting-started/core_concepts (workers/deployments/executions/events); the ~51,200
event / 50MB history cap and continue-as-new remedy (building-workflows/continue_as_new.md,
demonstrated in the shipped processor.py). Cap math is pure arithmetic.
"""
from __future__ import annotations

import mistralai.workflows as workflows

# The orchestration layer caps a single execution's event history. Past this, the workflow must
# have reset via continue_as_new or it fails. Value per the platform limit (~51,200 events).
HISTORY_EVENT_CAP = 51_200


def events_per_iteration(
    activities_per_iteration: int,
    events_per_activity: int = 3,
    workflow_task_events: int = 3,
) -> int:
    """History events one loop iteration adds.

    Each activity contributes ~3 events (scheduled / started / completed) and each iteration also
    drives one workflow task (~3 events: scheduled / started / completed). This is the estimator
    you use to reason about history growth; the exact per-activity count varies with signals and
    retries, so treat it as a planning number, not a guarantee.
    """
    return activities_per_iteration * events_per_activity + workflow_task_events


def iterations_until_cap(per_iteration: int, cap: int = HISTORY_EVENT_CAP) -> int:
    """How many iterations fit before the hard cap (floor). Beyond this the execution fails."""
    if per_iteration <= 0:
        raise ValueError("per_iteration must be positive")
    return cap // per_iteration


def safe_continue_as_new_cadence(
    per_iteration: int, cap: int = HISTORY_EVENT_CAP, safety_margin: float = 0.8
) -> int:
    """Iteration count at which to call continue_as_new, leaving headroom below the hard cap.

    Resetting at 80% of the cap (default) absorbs the extra events a final iteration, a signal, or
    a retry burst can add, so you reset on your terms rather than crashing at the ceiling.
    """
    if not 0.0 < safety_margin <= 1.0:
        raise ValueError("safety_margin must be in (0, 1]")
    return int((cap * safety_margin) // per_iteration)


@workflows.workflow.define(name="heartbeat-echo")
class HeartbeatEcho:
    """Minimal workflow that anchors the vocabulary: a worker in a deployment runs this execution,
    whose event history is what continue_as_new resets. One activity call, one echoed result."""

    @workflows.workflow.entrypoint
    async def run(self, message: str) -> dict:
        return {"echo": message}
