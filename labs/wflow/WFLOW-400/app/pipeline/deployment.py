"""WFLOW-400 Task 15 (L7.2): deployment routing, poller budget, and resetting a stuck run.

Three production concerns an operator owns at L400:

- **Routing / collision.** A worker registers its workflows under a `DEPLOYMENT_NAME`; the platform
  routes an execution to the deployment that registered its workflow name. If TWO deployments
  register the SAME name, routing is ambiguous and work can land on the wrong worker. The fix is a
  name unique per logical deployment; `resolve_routing` diagnoses the collision.
- **Poller budget.** Each worker runs a fixed number of task pollers. When many workers share one
  deployment (and a shared rate-limit key), you divide the total poller capacity across them so you
  neither starve nor oversubscribe the queue. `poller_budget` is that arithmetic.
- **Reset.** To recover a stuck or wrongly-progressed execution, `reset_workflow(execution_id,
  event_id, ...)` terminates the current run and restarts from a chosen point using the latest code.
  The event_id MUST be a `WORKFLOW_TASK_COMPLETED` event; `valid_reset_points` finds those from the
  execution's trace events.

Executable boundary (honest): the rate-limited activity registers via the real SDK (structural). The
routing-resolution, poller-budget, and reset-point selection are pure logic and run live, offline.
The live `reset_workflow` call and live routing need the platform — `reset_to_last_task` is shown
and source-checked.

Grounded in: managing-workflows-in-production/reset_workflow.md (`reset_workflow(execution_id,
event_id, reason, exclude_signals, exclude_updates)`; reset points from
`get_workflow_execution_trace_events(include_internal_events=True)` filtered to
`WORKFLOW_TASK_COMPLETED`); WFLOW-200 scale.py (`RateLimit(key=)`); worker config
(`DEPLOYMENT_NAME`, `max_*_task_pollers`).
"""
from __future__ import annotations

from typing import Any

import mistralai.workflows as workflows
from mistralai.workflows import RateLimit

# The worker reads this from its environment at startup. Executions route by this value; two
# deployments that register the same workflow name are distinguished only by it.
DEPLOYMENT_NAME_ENV = "DEPLOYMENT_NAME"

RATE_LIMIT_KEY = "partner-api"  # every activity with this key shares one budget across workers


@workflows.activity(
    name="fetch-partner-data",
    rate_limit=RateLimit(time_window_in_sec=60, max_execution=100, key=RATE_LIMIT_KEY),
)
async def fetch_partner_data(account_id: str) -> dict:
    # Capped to 100 executions / 60s across every workflow sharing the "partner-api" key, protecting
    # a downstream quota no matter how many runs fan out.
    return {"account_id": account_id, "rows": 3}


@workflows.workflow.define(name="deployment-ops-workflow")
class DeploymentOpsWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, account_id: str) -> dict:
        return await fetch_partner_data(account_id)


def resolve_routing(workflow_name: str, registrations: dict[str, list[str]]) -> dict:
    """Diagnose which deployment a workflow name routes to (offline, pure logic).

    `registrations` maps deployment_name -> the workflow names it registered. Zero matches is
    unrouted; more than one is an ambiguous collision that must be fixed by renaming.
    """
    owners = [dep for dep, names in registrations.items() if workflow_name in names]
    if not owners:
        return {"status": "unrouted", "deployment": None}
    if len(owners) > 1:
        return {"status": "ambiguous", "deployment": None, "collision": owners}
    return {"status": "routed", "deployment": owners[0]}


def poller_budget(total_poller_capacity: int, n_workers: int) -> int:
    """Pollers per worker so the deployment neither starves nor oversubscribes the queue (offline).

    Divide the deployment's total poller capacity evenly across its workers (floor, at least 1).
    """
    if n_workers <= 0:
        raise ValueError("n_workers must be positive")
    return max(1, total_poller_capacity // n_workers)


def valid_reset_points(events: list[Any]) -> list[int]:
    """Reset points from an execution's trace events: only WORKFLOW_TASK_COMPLETED event ids are
    valid targets for reset_workflow (offline, pure logic)."""
    return [
        e["event_id"]
        for e in events
        if e.get("event_type") == "WORKFLOW_TASK_COMPLETED"
    ]


def reset_to_last_task(client: Any, execution_id: str) -> Any:
    """Reset a stuck execution to its last completed workflow task (live reset is platform-only).

    `client` is an authenticated `mistralai.client.Mistral`. This reaches the live platform, so it
    is not run offline — the lab checks this call SHAPE and the reset-point logic structurally.
    """
    events = client.workflows.executions.get_workflow_execution_trace_events(
        execution_id=execution_id,
        include_internal_events=True,
    )
    points = [e.event_id for e in events if e.event_type == "WORKFLOW_TASK_COMPLETED"]
    return client.workflows.executions.reset_workflow(
        execution_id=execution_id,
        event_id=points[-1],
        reason="reset to last completed task after a stuck run",
        exclude_signals=True,
        exclude_updates=True,
    )
