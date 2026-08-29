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

Grounded in: managing-workflows-in-production/concurrency.md (executor table + parameter matrix).
"""
from __future__ import annotations

import mistralai.workflows as workflows


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
