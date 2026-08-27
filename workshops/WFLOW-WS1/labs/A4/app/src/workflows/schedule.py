"""A4: schedule definition for the nightly reconciliation workflow.

Scheduling is declared on the workflow with the `schedules=[...]` argument of
@workflow.define. This module builds the ScheduleDefinition and exports it as
SCHEDULE; reconciliation.py imports SCHEDULE and attaches it to the workflow. The
worker registers the schedule with the platform at startup, so a schedule change
takes effect only after you restart the worker.

Notes:
- ScheduleDefinition, SchedulePolicy, and ScheduleOverlapPolicy import from
  `mistralai.workflows.models`.
- Cron uses the standard 5-field syntax: "minute hour day-of-month month
  day-of-week". A definition can carry multiple cron_expressions, each of which
  triggers independently. Times are UTC by default.
- Each schedule passes its own `input` payload to the workflow entrypoint.
- Overlap policy defaults to SKIP; catchup_window_seconds bounds how far back a
  missed run may be caught up. Other overlap policies: BUFFER_ONE, ALLOW_ALL.

Production note: the canonical way to register a schedule is the client method
`client.workflows.schedules.schedule_workflow(workflow_identifier=..., schedule=...)`.
It returns a `WorkflowScheduleResponse` carrying a `schedule_id` and is managed out
of band with no worker restart, via `client.workflows.schedules.get_schedules()`,
`update_schedule(schedule_id=..., schedule=PartialScheduleDefinition(...))`, and
`unschedule_workflow(schedule_id=...)` (or the REST API under
`/v1/workflows/schedules`). The `schedules=[...]` decorator used above is now
deprecated (a decorator-defined schedule changes only after a worker restart), but
this self-contained single-worker lab uses it for simplicity and verify.py checks
for it. Prefer the client method in production.

[VERIFY] deployment_name / the schedule-to-deployment binding is
environment-specific. Deployments are discoverable via
`client.workflows.deployments.list_deployments(workflow_name=..., active_only=False)`
-> `.deployments[].name`; confirm the exact binding against your environment.
"""
from mistralai.workflows.models import (
    ScheduleDefinition,
    ScheduleOverlapPolicy,
    SchedulePolicy,
)

# The accounts the nightly run should reconcile. This dict is deserialized into
# the workflow entrypoint's typed input.
SCHEDULE_INPUT = {"account_ids": ["acct-001", "acct-002", "acct-003"]}

# 02:00 every day, UTC. "minute hour day-of-month month day-of-week".
CRON_EXPRESSIONS = ["0 2 * * *"]


def build_schedule_definition() -> ScheduleDefinition:
    """Return the schedule definition for the nightly reconciliation run."""
    return ScheduleDefinition(
        input=SCHEDULE_INPUT,
        cron_expressions=CRON_EXPRESSIONS,
        policy=SchedulePolicy(
            catchup_window_seconds=86400,  # catch up a missed run within 1 day
            overlap=ScheduleOverlapPolicy.SKIP,  # do not overlap runs
        ),
    )


# Exported for the @workflow.define(schedules=[SCHEDULE]) decorator and for
# verify.py to inspect offline.
SCHEDULE = build_schedule_definition()
