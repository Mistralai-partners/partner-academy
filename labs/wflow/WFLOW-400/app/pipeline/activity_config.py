"""WFLOW-400 Task 3 (L2.1): configure an activity, then defend its retry budget.

A single activity that calls a flaky external API must not block forever, must retry a transient
failure, must be noticed when it stalls mid-run, and must be named so it is legible in a trace.
Those concerns map to four decorator arguments:

- `start_to_close_timeout` — the wall-clock cap on ONE attempt; without it a hung call blocks
  indefinitely.
- `retry_policy_max_attempts` + `retry_policy_backoff_coefficient` — retry a transient failure with
  exponential backoff (2.0 doubles the delay each attempt).
- `heartbeat_timeout` — for a long call, require periodic `workflows.activity_heartbeat(...)` so the
  platform fails a stalled attempt fast instead of waiting out the full timeout.
- explicit `name=` — a stable activity name so the step is identifiable across versions and traces.

The L400 add is the budget arithmetic: before you set `max_attempts`, compute the worst-case delay
retries add so you know the failure-surfacing latency. That math is the shipped `retry_budget`
module, reused here so config and budget stay one lesson. Failure isolation is the second half:
the hardened fetch and the persist step are SEPARATE activities, so only the failing step retries.

Executable boundary (honest): the decorator config and heartbeat call are real SDK constructs,
checked structurally (metadata + registration + source). The budget math runs live via
`retry_budget`. A real retry needs the orchestrator.

Grounded in: building-workflows/activities/basics.md (Timeouts / Retry policies / Heartbeat);
shipped retry_budget.py (T-budget math); WFLOW-200 activity_config.py (proven decorator shape).
"""
from __future__ import annotations

from datetime import timedelta

import mistralai.workflows as workflows


@workflows.activity(
    name="fetch-quote",
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=5,
    retry_policy_backoff_coefficient=2.0,
    heartbeat_timeout=timedelta(seconds=15),
)
async def fetch_quote(symbol: str) -> dict:
    """Flaky pricing call: timeout caps the attempt, retries cover transient failures, the
    heartbeat lets the platform detect a stall before the full timeout elapses."""
    return {"symbol": symbol, "price": 100.0}


@workflows.activity(
    name="poll-price",
    start_to_close_timeout=timedelta(minutes=5),
    heartbeat_timeout=timedelta(seconds=15),
)
async def poll_price(symbol: str) -> dict:
    """A LONG activity checkpoints with activity_heartbeat(...) each tick; a missed heartbeat past
    heartbeat_timeout fails the attempt fast instead of waiting out the 5-minute timeout."""
    last = 0.0
    for tick in range(3):
        last = 100.0 + tick
        workflows.activity_heartbeat({"symbol": symbol, "tick": tick})
    return {"symbol": symbol, "price": last}


@workflows.activity(name="persist-quote", start_to_close_timeout=timedelta(seconds=60))
async def persist_quote(symbol: str, price: float) -> int:
    """Isolated write: composing this as its OWN activity means only the persist step retries if
    the write fails, not the (already succeeded) fetch."""
    return 1


@workflows.workflow.define(name="quote-config-workflow")
class QuoteConfigWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, symbol: str) -> dict:
        # Compose small, independently-retryable activities for failure isolation.
        quote = await fetch_quote(symbol)
        await persist_quote(symbol, quote["price"])
        return quote
