"""WFLOW-200 Task 8 (SOLUTION): publish a token stream and resume it without gaps.

A long activity (an LLM generation, a batch transform) should report progress as it runs so a
UI can render tokens in real time. You publish that progress with the `task(...)` context
manager: entering it opens an observable task, and `update_state(...)` emits an in-progress event
each time you have new output. Every emitted event carries a `broker_sequence` that is ordered,
unique, and resume-safe.

The consumer skill is the resume rule. When a connection drops, you reconnect with
`start_seq = last_broker_sequence + 1`, so nothing repeats and nothing is skipped. Resuming with
the last sequence you saw re-delivers that event (a duplicate); resuming from 0 replays the whole
stream. Reconnects also back off so a flapping connection does not hammer the broker.

Executable boundary (honest): live token emission needs a running worker connected to the
Workflows API, so `stream_tokens` is shown and checked structurally. The resume decisions you own
(`next_start_seq`, `reconnect_backoff`) are pure logic and run live, offline.

Grounded in: installed mistralai-workflows==3.10.0 — `task()` / `Task` observable context manager
(core/task/task.py: "async with task('llm_generation', state={'tokens': 0}) as t"); consumer
resume `start_seq = broker_sequence + 1` (protocol/v1/streaming.py, testing/workflow_helpers.py).
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def stream_tokens(prompt: str, n: int = 5) -> int:
    """Publish a token stream as it is produced. Each update emits an in-progress event
    (carrying a broker_sequence) that a UI can render live."""
    produced = 0
    # `task(...)` opens an observable task; update_state emits progress events to the API.
    async with workflows.task("token-stream", state={"tokens": 0}) as t:
        for i in range(n):
            produced = i + 1
            await t.update_state({"tokens": produced})  # emits one in-progress event
    return produced


@workflows.workflow.define(name="streaming-workflow")
class StreamingWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, prompt: str) -> dict:
        produced = await stream_tokens(prompt)
        return {"tokens": produced}


# ---- Consumer resume logic (pure, runs live offline) --------------------------------
def next_start_seq(last_broker_sequence: int) -> int:
    """Resume offset after seeing `last_broker_sequence`: the NEXT sequence, so nothing repeats
    and nothing is skipped. start_seq is inclusive, so you advance by exactly one."""
    return last_broker_sequence + 1


def reconnect_backoff(attempt: int, base: float = 0.5, cap: float = 8.0) -> float:
    """Exponential backoff for reconnect attempt N (0-based), capped so it never runs away."""
    return min(cap, base * (2 ** attempt))
