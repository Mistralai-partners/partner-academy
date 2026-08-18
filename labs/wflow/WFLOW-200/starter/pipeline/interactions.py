"""WFLOW-200 Task 3 (STARTER): interact with a running workflow via signal, query, update.

`OrderWorkflow` can start but the outside world cannot talk to it: there is no way to cancel
a running order, no way to read its current status, and no way to add an item and get the new
total back in one call. Add a handler for each of the three needs per tasks.md T3 — choosing
the right interaction primitive for each need is the point of the task, so decide before you
wire.

Grounded in: interacting-with-workflows/{signals,queries,updates}.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def price_item(sku: str) -> float:
    return float(len(sku))


@workflows.workflow.define(name="order-workflow")
class OrderWorkflow:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.total: float = 0.0
        self.cancelled: bool = False

    # TODO(T3): the outside world must be able to cancel a running order — fire-and-forget,
    # no return value. Add the handler named "cancel_order" that sets self.cancelled = True,
    # using the interaction primitive that fits that need (decide which; see the comparison
    # table in the docs).

    # TODO(T3): a caller must read the current status (items/total/cancelled) WITHOUT changing
    # anything. Add the read-only handler named "get_status" using the primitive that fits.

    # TODO(T3): a caller must add an item AND get the new total back in one call — which means
    # running the price_item activity. Add the handler named "add_item" that appends the sku,
    # adds to total, and RETURNS a confirmation dict, using the primitive that both mutates
    # state and returns a value.

    @workflows.workflow.entrypoint
    async def run(self) -> dict:
        await workflows.workflow.wait_condition(lambda: self.cancelled)
        return {"final_total": self.total, "cancelled": self.cancelled}
