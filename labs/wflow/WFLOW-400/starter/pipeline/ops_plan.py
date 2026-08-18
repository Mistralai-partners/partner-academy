"""WFLOW-400 Task 5 (STARTER): production ops decisions with the wrong choices.

Two fixes:
  (a) The sync schedule uses BUFFER_ALL, which queues every missed run and builds an unbounded
      backlog. For a job where only the latest data matters, choose SKIP instead.
  (b) choose_executor returns "offset" even when the whole collection is already known. A fully
      materialized collection should use the List executor.

Reference: ../../solution/pipeline/ops_plan.py, scheduling.md, concurrency.md.
"""
from __future__ import annotations

from mistralai.workflows.models import (
    ScheduleDefinition,
    SchedulePolicy,
    ScheduleOverlapPolicy,
)


def latest_only_sync_schedule() -> ScheduleDefinition:
    return ScheduleDefinition(
        input={"source": "postgres"},
        cron_expressions=["*/5 * * * *"],
        # BUG: BUFFER_ALL builds an unbounded backlog; only the latest sync matters here.
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ALL),
    )


def choose_executor(scenario: dict) -> dict:
    # BUG: always returns offset pagination, even for a fully materialized collection.
    return {
        "executor": "offset",
        "kwargs": {
            "get_item_from_index_activity": "<activity>",
            "n_items": scenario.get("n_items"),
            "max_concurrent_executions_per_worker": 50,
        },
    }
