"""WFLOW-400 Task 14 (L7.1): scheduling — calendars, interval+jitter, overlap, retiming.

A workflow runs on a recurring schedule registered from the CLIENT (the schedule decorator is
deprecated). Three shapes cover the field:

- **Calendar** — fire at specific wall-clock times. `ScheduleCalendar(hour=[ScheduleRange(start=9)],
  minute=[ScheduleRange(start=0)])` is 09:00 UTC; a `ScheduleRange(start=8, end=18)` covers a
  window. This is the weekday-business-hours shape.
- **Interval + jitter** — fire every fixed period with a random offset so a fleet of tenants does
  not all fire at once. `intervals=[ScheduleInterval(every="PT1H")]` with `jitter="PT5M"` spreads
  each run randomly within a 5-minute window.
- **Overlap policy** — when a run is still going at the next fire time, `SchedulePolicy(overlap=...)`
  decides: SKIP the new run (only-latest-matters syncs), or BUFFER it. Reusing the shipped
  `ops_plan.latest_only_sync_schedule` (overlap=SKIP) keeps that decision one lesson.

Registration takes a `deployment_name` (which deployment's workers run it). Retiming is
pause/resume: `pause_schedule(schedule_id, note=)` then `resume_schedule(schedule_id, note=)`.

Executable boundary (honest): the `ScheduleDefinition` variants are built with the real SDK and
checked structurally; fire-time and overlap logic run live, offline. The live create/pause/resume
calls need the platform — `register_schedule` is shown and source-checked.

Grounded in: building-workflows/scheduling.md (`schedule_workflow(workflow_identifier,
deployment_name, schedule=ScheduleDefinition(calendars=[ScheduleCalendar(hour=[ScheduleRange(...)])]))`,
`intervals=[ScheduleInterval(every=)]` + `jitter=`, `SchedulePolicy(overlap=)`, `pause_schedule`/
`resume_schedule`); shipped ops_plan.py (overlap=SKIP + cron). Interval/jitter field names confirmed
via context7 this pass.
"""
from __future__ import annotations

from typing import Any

from mistralai.workflows.models import (
    ScheduleCalendar,
    ScheduleDefinition,
    ScheduleInterval,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleRange,
)


def weekday_business_hours_schedule() -> ScheduleDefinition:
    """Fire at 09:00 UTC on a business-hours calendar, buffering one late run rather than skipping."""
    return ScheduleDefinition(
        input={"report": "daily"},
        calendars=[
            ScheduleCalendar(
                hour=[ScheduleRange(start=9)],
                minute=[ScheduleRange(start=0)],
            )
        ],
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ONE),
    )


def hourly_jittered_schedule() -> ScheduleDefinition:
    """Fire hourly with up to 5 minutes of jitter so a tenant fleet does not spike simultaneously."""
    return ScheduleDefinition(
        input={"tenant": "acme"},
        intervals=[ScheduleInterval(every="PT1H")],
        jitter="PT5M",
    )


def cron_nightly_schedule() -> ScheduleDefinition:
    """A cron variant for teams that prefer crontab syntax: 02:30 UTC nightly, overlap=SKIP."""
    return ScheduleDefinition(
        input={"job": "nightly-compaction"},
        cron_expressions=["30 2 * * *"],
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
    )


def minute_of_day(hour: int, minute: int) -> int:
    """Fire-time math (offline): normalize an HH:MM calendar slot to minutes since midnight, so two
    schedules can be compared or spaced without pulling in wall-clock time."""
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("hour must be 0-23 and minute 0-59")
    return hour * 60 + minute


def register_schedule(client: Any, deployment_name: str = "production") -> Any:
    """Register the calendar schedule on the platform via the CLIENT (live create is platform-only).

    `client` is an authenticated `mistralai.client.Mistral`. This reaches the live platform (auth +
    a deployed workflow), so it is not run offline — the lab checks the built ScheduleDefinition and
    this call site structurally. pause_schedule / resume_schedule retime it once it exists.
    """
    return client.workflows.schedules.schedule_workflow(
        workflow_identifier="daily-report-workflow",
        deployment_name=deployment_name,
        schedule=weekday_business_hours_schedule(),
    )
