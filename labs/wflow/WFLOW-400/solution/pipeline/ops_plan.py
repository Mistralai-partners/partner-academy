"""WFLOW-400 Task 5 (SOLUTION): production ops decisions under competing constraints.

(a) Schedule overlap policy. For a sync job where only the latest data matters and a slow run
    must never build a backlog, the right policy is SKIP (drop the new run). BUFFER_ALL would
    queue every missed run and create an unbounded backlog. (scheduling.md overlap table)

(b) Concurrency executor selection. execute_activities_in_parallel offers three patterns:
      - List executor   -> a fully materialized collection you have upfront.
      - Chain executor   -> a stream/queue paged by an opaque continuation token.
      - Offset executor  -> index/offset pagination where you fetch page N by number.
    (concurrency.md)
"""
from __future__ import annotations

from mistralai.workflows.models import (
    ScheduleDefinition,
    SchedulePolicy,
    ScheduleOverlapPolicy,
)


def latest_only_sync_schedule() -> ScheduleDefinition:
    """A 5-minute sync where only the latest data matters -> overlap = SKIP."""
    return ScheduleDefinition(
        input={"source": "postgres"},
        cron_expressions=["*/5 * * * *"],
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
    )


def choose_executor(scenario: dict) -> dict:
    """Return the execute_activities_in_parallel plan (executor kind + key kwargs) for a scenario."""
    if scenario.get("all_items_known"):
        return {
            "executor": "list",
            "kwargs": {"items": "<materialized list>", "max_concurrent_scheduled_tasks": 100},
        }
    if scenario.get("continuation_token"):
        return {
            "executor": "chain",
            "kwargs": {"get_item_from_prev_item_activity": "<activity>"},
        }
    return {
        "executor": "offset",
        "kwargs": {
            "get_item_from_index_activity": "<activity>",
            "n_items": scenario.get("n_items"),
            "max_concurrent_executions_per_worker": 50,
            "max_concurrent_scheduled_tasks": 100,
        },
    }
