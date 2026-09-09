"""WFLOW-200 Task 2 (SOLUTION): configure an activity's timeout, retries, and heartbeat.

An activity that calls a flaky external API must not block forever, must retry a transient
failure, and must let the platform notice when it goes unresponsive mid-run. Those three
concerns map to three decorator arguments:

- `start_to_close_timeout` — the wall-clock cap on a single attempt; without it an
  unresponsive call blocks indefinitely.
- `retry_policy_max_attempts` + `retry_policy_backoff_coefficient` — retry a transient
  failure automatically with exponential backoff (2.0 doubles the delay each attempt).
- `heartbeat_timeout` — for a long call, require periodic `workflows.activity_heartbeat(...)` so the
  platform can fail-fast a stalled attempt instead of waiting out the full timeout.

Grounded in: building-workflows/activities/basics.md (Timeouts / Retry policies / Heartbeat).
"""
from __future__ import annotations

from datetime import timedelta

import mistralai.workflows as workflows
from mistralai.workflows import activity


@workflows.activity(
    name="fetch_quote",
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=5,
    retry_policy_backoff_coefficient=2.0,
    heartbeat_timeout=timedelta(seconds=15),
)
async def fetch_quote(symbol: str) -> dict:
    """Call a flaky pricing API. Timeout caps the attempt; retries cover transient failures;
    the heartbeat lets the platform detect a stall before the full timeout elapses."""
    # A real implementation would call the pricing API here and heartbeat during long work:
    #   workflows.activity_heartbeat({"symbol": symbol})
    return {"symbol": symbol, "price": 100.0}


# A small, single-purpose activity. Composing several of these beats nesting the whole job in
# one mega-activity: each step stays independently retryable and visible in the execution trace.
@workflows.activity(name="normalize_symbol")
async def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


# A LONG-running activity checkpoints with activity_heartbeat(...) so the platform can fail-fast a
# stalled attempt before the full start_to_close_timeout elapses (paired with heartbeat_timeout).
@workflows.activity(
    name="poll_price",
    start_to_close_timeout=timedelta(minutes=5),
    heartbeat_timeout=timedelta(seconds=15),
)
async def poll_price(symbol: str) -> dict:
    last = 0.0
    for tick in range(3):
        last = 100.0 + tick
        # Report progress each tick; a missed heartbeat past heartbeat_timeout fails the attempt.
        workflows.activity_heartbeat({"symbol": symbol, "tick": tick})
    return {"symbol": symbol, "price": last}


@workflows.workflow.define(name="quote-workflow")
class QuoteWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, symbol: str) -> dict:
        # Compose small activities rather than nesting the whole job in one:
        # normalize, then fetch the (configured, retried, heartbeating) quote.
        normalized = await normalize_symbol(symbol)
        return await fetch_quote(normalized)
