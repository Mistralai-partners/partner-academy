"""WFLOW-200 Task 11 (SOLUTION): run work concurrently and cap a shared quota.

Two everyday scaling skills:

- **Concurrency.** For a small batch, `asyncio.gather` over a handful of activity calls is enough.
  Past roughly ten thousand items it stops being enough (it materializes every call at once), and
  you move to `execute_activities_in_parallel` with the right executor. The List executor is the
  one for a collection you already hold; it tunes with `max_concurrent_scheduled_tasks`.
- **Rate limiting.** A hot activity that shares a downstream quota (one flaky partner API) carries
  a `RateLimit(time_window_in_sec, max_execution, key=...)` on its decorator. The `key` groups
  every activity that shares the SAME budget, so the limit holds across workflows, not per call
  site.

Executable boundary (honest): `execute_activities_in_parallel` and the rate limit are enforced by
the running worker, so the executor plan and the rate-limit decorator are checked structurally;
the small-batch `asyncio.gather` path and the plan selection run live, offline.

Grounded in: managing-workflows-in-production/concurrency.md; installed
mistralai-workflows==3.10.0 — `execute_activities_in_parallel` + `max_concurrent_scheduled_tasks`
(core/execution/concurrency/), `RateLimit` (core/activity.py). Prior art: WFLOW-300 scale.py.
"""
from __future__ import annotations

import asyncio

import mistralai.workflows as workflows
from mistralai.workflows import RateLimit


@workflows.activity()
async def process_record(record_id: int, value: str) -> dict:
    return {"record_id": record_id, "result": f"processed:{value}"}


def choose_executor(scenario: dict) -> dict:
    """Return the execute_activities_in_parallel plan for a scenario.

    List executor -> you already hold the whole collection (the common L200 case).
    Offset executor -> index-addressable pages (a large dataset fetched page by page)."""
    if scenario.get("index_addressable"):
        return {
            "executor": "offset",
            "kwargs": {
                "n_items": scenario.get("n_items"),
                "max_concurrent_scheduled_tasks": 100,
            },
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


@workflows.workflow.define(name="batch-report-workflow")
class BatchReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, values: list[str]) -> dict:
        # Small batch: gather is the simplest way to fan out a handful of activities in parallel.
        results = await asyncio.gather(
            *(process_record(i, v) for i, v in enumerate(values))
        )
        return {"processed": len(results)}
