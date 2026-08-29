"""WFLOW-200 Task 3 (SOLUTION): interact with a running workflow via signal, query, update.

A long-running workflow needs three kinds of outside interaction, and each maps to a
different primitive (see the comparison table in signals/queries/updates docs):

- **signal** — asynchronous, one-way, modifies state, returns nothing. Use it to *tell*
  the workflow something ("cancel this order").
- **query** — synchronous, read-only, returns a value, never mutates. Use it to *read*
  current state ("what is the order status?").
- **update** — synchronous, mutates state, returns a value, and MAY run an activity. Use it
  when the caller must *change something and get a confirmation back* ("add this item, tell
  me the new total").

Grounded in: interacting-with-workflows/{signals,queries,updates}.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def price_item(sku: str) -> float:
    """Look up an item price. Real work (a catalog lookup) lives in an activity."""
    return float(len(sku))  # deterministic stand-in for a catalog price lookup


@workflows.workflow.define(name="order-workflow")
class OrderWorkflow:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.total: float = 0.0
        self.cancelled: bool = False

    @workflows.workflow.signal(name="cancel_order")
    async def cancel_order(self) -> None:
        # Asynchronous, no return value: the caller just tells us to cancel.
        self.cancelled = True

    @workflows.workflow.query(name="get_status")
    def get_status(self) -> dict:
        # Synchronous, read-only: return current state without mutating it.
        return {"items": list(self.items), "total": self.total, "cancelled": self.cancelled}

    @workflows.workflow.update(name="add_item")
    async def add_item(self, sku: str) -> dict:
        # Synchronous, mutates state, runs an activity, and returns confirmation.
        price = await price_item(sku)
        self.items.append(sku)
        self.total += price
        return {"added": sku, "price": price, "total": self.total}

    @workflows.workflow.entrypoint
    async def run(self) -> dict:
        # Suspend cheaply until the order is cancelled from the outside.
        await workflows.workflow.wait_condition(lambda: self.cancelled)
        return {"final_total": self.total, "cancelled": self.cancelled}
