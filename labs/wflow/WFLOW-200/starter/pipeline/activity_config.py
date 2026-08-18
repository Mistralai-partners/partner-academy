"""WFLOW-200 Task 2 (STARTER): configure an activity's timeout, retries, and heartbeat.

`fetch_quote` calls a flaky pricing API but is declared with a bare `@activity()`: no retry
policy and no heartbeat, so a transient failure is fatal and a stall is invisible until the
default timeout elapses. Configure it per tasks.md T2. Grounded in activities/basics.md.
"""
from __future__ import annotations

from datetime import timedelta  # noqa: F401  (you will need this)

import mistralai.workflows as workflows
from mistralai.workflows import activity  # noqa: F401


# TODO(T2): configure this activity with an explicit run timeout (start-to-close), a retry
# policy (max attempts + backoff coefficient), and a heartbeat timeout for the long call.
# See activities/basics.md for the exact decorator argument names.
@workflows.activity(name="fetch_quote")
async def fetch_quote(symbol: str) -> dict:
    return {"symbol": symbol, "price": 100.0}


@workflows.workflow.define(name="quote-workflow")
class QuoteWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, symbol: str) -> dict:
        return await fetch_quote(symbol)
