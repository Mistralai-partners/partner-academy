"""WFLOW-300 Task 4 (STARTER): the wrong concurrency executor at scale.

SYMPTOM: every scenario is routed through offset pagination, even a stream that only exposes
a continuation token and a collection that is already fully in memory. The List plan even
ships `max_concurrent_executions_per_worker`, a knob that only the Offset executor reads.

Diagnose which executor each source actually supports (index-addressable pages vs a
continuation-token stream vs a materialized list) and return the right plan and knobs for
each. Reference: ../../solution/pipeline/scale.py,
managing-workflows-in-production/concurrency.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def process_record(record_id: int, value: str) -> dict:
    return {"record_id": record_id, "result": f"processed:{value}"}


@workflows.activity()
async def get_record_by_index(params: workflows.GetItemFromIndexParams) -> dict:
    return {"record_id": params.idx, "value": f"record_{params.idx}"}


@workflows.activity()
async def get_next_record(prev: dict | None) -> dict | None:
    if prev is None:
        return {"record_id": 0, "value": "record_0"}
    nxt = prev["record_id"] + 1
    return None if nxt >= 1000 else {"record_id": nxt, "value": f"record_{nxt}"}


def choose_executor(scenario: dict) -> dict:
    # SYMPTOM: offset pagination for everything, regardless of how the source is addressable.
    return {
        "executor": "offset",
        "kwargs": {
            "get_item_from_index_activity": get_record_by_index,
            "n_items": scenario.get("n_items"),
            "max_concurrent_scheduled_tasks": 100,
            "max_concurrent_executions_per_worker": 100,
        },
    }
