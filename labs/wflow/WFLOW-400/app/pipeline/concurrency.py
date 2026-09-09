"""WFLOW-400 Task 12 (L6.1): concurrency patterns — List, Chain, Offset.

`execute_activities_in_parallel` runs an activity across many items with one of three patterns, and
the right one depends on HOW the source is addressable, not on item count:

  - **List** — you already hold the whole materialized collection. Pass `items=`; tune with
    `max_concurrent_scheduled_tasks`.
  - **Chain** — a stream paged by an opaque continuation token. Pass
    `get_item_from_prev_item_activity=`; discovery is sequential, processing parallel.
  - **Offset** — index-addressable pages (page numbers, SQL OFFSET/LIMIT). Pass
    `get_item_from_index_activity=` + `n_items=`; tune with BOTH
    `max_concurrent_scheduled_tasks` and `max_concurrent_executions_per_worker`.

For a small batch, `asyncio.gather` over a handful of activity calls is enough; past ~10k items you
move to `execute_activities_in_parallel`. Pair the executors with continue-as-new for very large
sets so history does not blow the cap. The selection rule is the shipped `ops_plan.choose_executor`.

Executable boundary (honest): `execute_activities_in_parallel` is enforced by the running worker, so
the List and Offset workflows are checked structurally (they register). The small-batch `gather`
path and the `choose_executor` selection run live, offline.

Grounded in: managing-workflows-in-production/concurrency.md (`execute_activities_in_parallel` +
List/Chain/Offset params, `GetItemFromIndexParams`); shipped ops_plan.py (`choose_executor`).
"""
from __future__ import annotations

import asyncio

from pydantic import BaseModel

import mistralai.workflows as workflows


@workflows.activity()
async def process_item(item_id: int, value: str) -> dict:
    return {"item_id": item_id, "result": f"processed:{value}"}


@workflows.activity()
async def get_item_by_index(params: workflows.GetItemFromIndexParams) -> dict:
    # Offset pagination: fetch the item at a numeric index.
    return {"item_id": params.idx, "value": f"item_{params.idx}"}


class ListRequest(BaseModel):
    values: list[str]


@workflows.workflow.define(name="list-concurrency-workflow")
class ListConcurrencyWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ListRequest) -> dict:
        # Small batch: gather is the simplest fan-out.
        small = await asyncio.gather(
            *(process_item(i, v) for i, v in enumerate(req.values))
        )
        # Larger, already-materialized collection: the List executor.
        items = [{"item_id": i, "value": v} for i, v in enumerate(req.values)]
        results = await workflows.execute_activities_in_parallel(
            activity=process_item,
            items=items,
            max_concurrent_scheduled_tasks=100,
        )
        return {"gathered": len(small), "listed": len(results or [])}


@workflows.workflow.define(name="offset-concurrency-workflow")
class OffsetConcurrencyWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, n_items: int) -> dict:
        # Index-addressable pages: the Offset executor, with both concurrency knobs.
        results = await workflows.execute_activities_in_parallel(
            activity=process_item,
            get_item_from_index_activity=get_item_by_index,
            n_items=n_items,
            max_concurrent_scheduled_tasks=100,
            max_concurrent_executions_per_worker=50,
        )
        return {"processed": len(results or [])}
