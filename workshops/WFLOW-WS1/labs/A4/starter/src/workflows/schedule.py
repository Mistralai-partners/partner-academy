"""A4 (starter): schedule definition STUB.

The reconciliation workflow is supposed to fire nightly, but right now nothing
schedules it. Scheduling is declared on the workflow with the `schedules=[...]`
argument of @workflow.define: this module builds a ScheduleDefinition and exports
it as SCHEDULE, and reconciliation.py attaches SCHEDULE to the workflow. The
worker registers schedules at startup, so a change takes effect only after a
worker restart.

Two things are missing here, plus the wiring in reconciliation.py. Full steps are
in TASKS.md.

Import note: ScheduleDefinition, SchedulePolicy, and ScheduleOverlapPolicy come
from `mistralai.workflows.models`. Cron is the 5-field syntax
"minute hour day-of-month month day-of-week", UTC by default.
"""
from mistralai.workflows.models import (  # noqa: F401 (used once the definition is completed)
    ScheduleDefinition,
    ScheduleOverlapPolicy,
    SchedulePolicy,
)

# The accounts the nightly run should reconcile. This dict is deserialized into
# the workflow entrypoint's typed input.
SCHEDULE_INPUT = {"account_ids": ["acct-001", "acct-002", "acct-003"]}


def build_schedule_definition() -> ScheduleDefinition:
    """Return the schedule definition for the nightly reconciliation run."""
    # TODO: definition incomplete: this schedule has no trigger and no input, so
    # it would never fire. A ScheduleDefinition needs at least one cron_expressions
    # entry (5-field, UTC) plus the workflow input, and should set an overlap and
    # catchup policy deliberately.
    return ScheduleDefinition(
        # input=...,
        # cron_expressions=[...],
    )


# TODO: this schedule is never registered: nothing attaches it to the workflow.
# Once the definition is complete, export it and wire it into
# reconciliation.py with @workflow.define(..., schedules=[SCHEDULE]).
SCHEDULE = build_schedule_definition()
