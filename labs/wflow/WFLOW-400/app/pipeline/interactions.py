"""WFLOW-400 Task 5 (L3.1): signal, query, update, and a wait condition.

A long-running workflow needs three kinds of outside interaction, and each maps to a different
primitive:

- **signal** — asynchronous, one-way, mutates state, returns nothing. Use it to TELL the workflow
  something ("cancel this order").
- **query** — synchronous, read-only, returns a value, never mutates. Use it to READ current state
  ("what is the order status?").
- **update** — synchronous, mutates state, returns a value, and MAY run an activity. Use it when the
  caller must CHANGE something and get a confirmation back ("add this item, tell me the new total").

The entrypoint suspends on `wait_condition` until a signal flips the predicate, at zero cost. The
L400 add is validating an update payload BEFORE it mutates state, so a bad request is rejected
locally instead of corrupting the workflow.

Executable boundary (honest): the three primitives register via the real SDK and are checked by
introspection. The payload-validation rule and the `price_item` activity run live. Delivering a
real signal/update needs the orchestrator.

Grounded in: interacting-with-workflows/{signals,queries,updates}.md; WFLOW-200 interactions.py
(proven `signal`/`query`/`update` + `wait_condition`).
"""
from __future__ import annotations

import mistralai.workflows as workflows


def validate_add_item(payload: dict) -> tuple[bool, str]:
    """Reject a bad add-item request locally, before the update mutates state (offline logic)."""
    sku = payload.get("sku")
    if not isinstance(sku, str) or not sku.strip():
        return (False, "sku must be a non-empty string")
    if payload.get("qty", 1) < 1:
        return (False, "qty must be >= 1")
    return (True, "ok")


@workflows.activity()
async def price_item(sku: str) -> float:
    """Real work (a catalog price lookup) lives in an activity."""
    return float(len(sku))  # deterministic stand-in for a catalog price


@workflows.workflow.define(name="order-interactions-workflow")
class OrderInteractionsWorkflow:
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
        # Validate first, then mutate + run an activity + return confirmation.
        good, detail = validate_add_item({"sku": sku})
        if not good:
            return {"added": None, "error": detail, "total": self.total}
        price = await price_item(sku)
        self.items.append(sku)
        self.total += price
        return {"added": sku, "price": price, "total": self.total}

    @workflows.workflow.entrypoint
    async def run(self) -> dict:
        # Suspend cheaply until the order is cancelled from the outside.
        await workflows.workflow.wait_condition(lambda: self.cancelled)
        return {"final_total": self.total, "cancelled": self.cancelled}
