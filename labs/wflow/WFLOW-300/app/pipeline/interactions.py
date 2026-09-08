"""WFLOW-300 Task 8 (SOLUTION): drive a running workflow with signal + query + update.

A long-lived workflow that holds state needs three different doors to the outside, and mixing
them up is the common mistake. Each maps to one primitive (see the comparison table in the
signals/queries/updates docs):

- **signal** — asynchronous, one-way, mutates state, returns nothing. Use it to *tell* the
  workflow something ("release this reservation").
- **query** — synchronous, read-only, returns a value, never mutates. Use it to *read* the
  current state ("what does the reservation hold right now?").
- **update** — synchronous, mutates state, returns a value, and MAY run an activity. Use it
  when the caller must *change something and get a confirmation back* ("add a guest, and tell
  me the new party total").

The load-bearing detail at L300 depth: the update delegates its real work to an activity
(the price lookup), because an update may run activities while a query may not.

Grounded in: interacting-with-workflows/{signals,queries,updates}.md,
building-workflows/waiting_for_conditions.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def price_guest(tier: str) -> float:
    """Look up the per-guest price for a fare tier. Real work (a catalog lookup) lives in an
    activity so the update handler stays a thin, deterministic wrapper."""
    return float(len(tier))  # deterministic stand-in for a pricing lookup


@workflows.workflow.define(name="reservation-workflow")
class ReservationWorkflow:
    def __init__(self) -> None:
        self.guests: list[str] = []
        self.total: float = 0.0
        self.released: bool = False

    @workflows.workflow.signal(name="release")
    async def release(self) -> None:
        # Asynchronous, no return value: the caller just tells us to let the hold go.
        self.released = True

    @workflows.workflow.query(name="get_state")
    def get_state(self) -> dict:
        # Synchronous, read-only: return current state without mutating it.
        return {"guests": list(self.guests), "total": self.total, "released": self.released}

    @workflows.workflow.update(name="add_guest")
    async def add_guest(self, tier: str) -> dict:
        # Synchronous, mutates state, runs an activity, and returns confirmation.
        price = await price_guest(tier)
        self.guests.append(tier)
        self.total += price
        return {"added": tier, "price": price, "total": self.total}

    @workflows.workflow.entrypoint
    async def run(self) -> dict:
        # Suspend cheaply until the reservation is released from the outside.
        await workflows.workflow.wait_condition(lambda: self.released)
        return {"final_total": self.total, "released": self.released}
