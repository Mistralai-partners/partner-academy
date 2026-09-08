"""WFLOW-300 Task 4 (SOLUTION): choose the right concurrency executor at scale.

`execute_activities_in_parallel` offers three executors, and the right one depends on HOW
the source is addressable, not on how many items there are:

  - List executor   -> you already hold the whole materialized collection.
                       Tunes with max_concurrent_scheduled_tasks only.
  - Chain executor   -> a stream paged by an opaque continuation token (S3 ContinuationToken,
                       DynamoDB LastEvaluatedKey). Discovery is sequential; processing is parallel.
                       Takes neither concurrency knob.
  - Offset executor  -> index-addressable pages (REST page numbers, SQL OFFSET/LIMIT). This is
                       the right choice for 500k records fetched page-by-page. Tunes with BOTH
                       max_concurrent_scheduled_tasks AND max_concurrent_executions_per_worker.

`max_concurrent_executions_per_worker` is an OFFSET-ONLY knob; putting it on a List plan is a
tell that the executor was chosen wrong.

Scale has two more levers this module also covers:

  - **Rate limiting** — a hot activity that shares a downstream quota (one flaky partner API)
    carries a `RateLimit(time_window_in_sec, max_execution, key=...)` on its decorator. The
    `key` groups every activity that shares the SAME budget, so the limit is enforced across
    workflows, not per call site.
  - **Scheduling** — a workflow is scheduled from the CLIENT with
    `client.workflows.schedules.schedule_workflow(schedule=ScheduleDefinition(...),
    workflow_identifier=...)`. This is the canonical path; the old schedule DECORATOR is
    deprecated and is deliberately not used here. Overlap policy (e.g. SKIP) keeps a slow run
    from building a backlog.

Grounded in: managing-workflows-in-production/concurrency.md (executor table + parameter matrix);
installed mistralai-workflows==3.10.0 introspection — `activity(rate_limit=RateLimit(...))`
(core/activity.py), `RateLimit(time_window_in_sec, max_execution, key)`, and the client method
`Mistral().workflows.schedules.schedule_workflow(schedule=ScheduleDefinition, workflow_identifier)`
(client/schedules.py); WFLOW-400 ops_plan.py (`ScheduleDefinition` + overlap policy).
"""
from __future__ import annotations

from typing import Any

import mistralai.workflows as workflows
from mistralai.workflows import RateLimit
from mistralai.workflows.models import (
    ScheduleDefinition,
    ScheduleOverlapPolicy,
    SchedulePolicy,
)


@workflows.activity()
async def process_record(record_id: int, value: str) -> dict:
    return {"record_id": record_id, "result": f"processed:{value}"}


@workflows.activity()
async def get_record_by_index(params: workflows.GetItemFromIndexParams) -> dict:
    # Offset pagination: fetch the item at a numeric index.
    return {"record_id": params.idx, "value": f"record_{params.idx}"}


@workflows.activity()
async def get_next_record(prev: dict | None) -> dict | None:
    # Chain pagination: derive the next item from the previous one; None ends the stream.
    if prev is None:
        return {"record_id": 0, "value": "record_0"}
    nxt = prev["record_id"] + 1
    return None if nxt >= 1000 else {"record_id": nxt, "value": f"record_{nxt}"}


def choose_executor(scenario: dict) -> dict:
    """Return the execute_activities_in_parallel plan (executor kind + kwargs) for a scenario."""
    if scenario.get("index_addressable"):
        # e.g. 500k records fetched by page number / OFFSET.
        return {
            "executor": "offset",
            "kwargs": {
                "get_item_from_index_activity": get_record_by_index,
                "n_items": scenario["n_items"],
                "max_concurrent_scheduled_tasks": 100,
                "max_concurrent_executions_per_worker": 100,
            },
        }
    if scenario.get("continuation_token"):
        return {
            "executor": "chain",
            "kwargs": {"get_item_from_prev_item_activity": get_next_record},
        }
    return {
        "executor": "list",
        "kwargs": {
            "items": scenario.get("items", []),
            "max_concurrent_scheduled_tasks": 100,
        },
    }


# ---- Rate limiting: cap a shared-quota activity across all callers -------------------
RATE_LIMIT_KEY = "partner-api"  # every activity with this key shares one budget


@workflows.activity(
    name="fetch-partner-data",
    rate_limit=RateLimit(time_window_in_sec=60, max_execution=100, key=RATE_LIMIT_KEY),
)
async def fetch_partner_data(account_id: str) -> dict:
    # The RateLimit caps this call to 100 executions / 60s across every workflow that shares the
    # "partner-api" key, protecting a downstream quota no matter how many runs fan out.
    return {"account_id": account_id, "rows": 3}


@workflows.workflow.define(name="daily-report-workflow")
class DailyReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, account_id: str) -> dict:
        return await fetch_partner_data(account_id)


# ---- Scheduling: register a recurring run from the CLIENT (decorator is deprecated) ---
def build_report_schedule() -> ScheduleDefinition:
    """A daily report at 06:00, with overlap=SKIP so a slow run never builds a backlog."""
    return ScheduleDefinition(
        input={"account_id": "acct-1"},
        cron_expressions=["0 6 * * *"],
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
    )


def schedule_daily_report(client: Any) -> Any:
    """Register the schedule on the platform via the CLIENT.

    `client` is an authenticated `mistralai.client.Mistral`. This call reaches the live platform
    (auth + a registered/deployed workflow), so it runs against a real deployment, not offline —
    the lab checks the schedule SHAPE (built above) and this call site structurally.
    """
    return client.workflows.schedules.schedule_workflow(
        schedule=build_report_schedule(),
        workflow_identifier="daily-report-workflow",
    )
