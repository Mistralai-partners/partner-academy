"""WFLOW-400 Task 9 (L5.1): publish a streaming event with an ordered broker_sequence.

A long activity (an LLM generation, a batch transform) should report progress as it runs so a UI
can render it live. You publish that progress with the `task(...)` context manager: entering it
opens an observable task, and `update_state(...)` emits an in-progress event each time there is new
output. Every emitted event carries a `broker_sequence` that is ordered, unique, and resume-safe,
and payloads must stay under the platform size limit.

The consumer counterpart is the resume rule you own here: after seeing an event, the next read
starts at `broker_sequence + 1`, so nothing repeats and nothing is skipped. (Consuming the stream
end to end is Task 10.)

Executable boundary (honest): live event emission needs a running worker connected to the platform,
so `stream_tokens` is shown and checked structurally (publish-side present + registration). The
resume arithmetic (`next_start_seq`) is pure logic and runs live, offline.

Grounded in: building-workflows/streaming.md (`task()` / `update_state`, "Sequence Guarantee");
WFLOW-200 streaming.py (proven publish-side `task()`/`update_state` + resume math).
"""
from __future__ import annotations

import mistralai.workflows as workflows


@workflows.activity()
async def stream_tokens(prompt: str, n: int = 5) -> int:
    """Publish a token stream as it is produced. Each update emits an in-progress event (carrying a
    broker_sequence) that a UI can render live."""
    produced = 0
    async with workflows.task("token-stream", state={"tokens": 0}) as t:
        for i in range(n):
            produced = i + 1
            await t.update_state({"tokens": produced})  # emits one in-progress event
    return produced


@workflows.activity()
async def stream_progress(total: int) -> int:
    """A progress stream: emit percent-complete as an ordered sequence of in-progress events."""
    async with workflows.task("progress-stream", state={"pct": 0}) as t:
        for done in range(1, total + 1):
            await t.update_state({"pct": int(done / total * 100)})
    return total


@workflows.workflow.define(name="streaming-publish-workflow")
class StreamingPublishWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, prompt: str) -> dict:
        tokens = await stream_tokens(prompt)
        steps = await stream_progress(4)
        return {"tokens": tokens, "steps": steps}


# ---- Consumer resume arithmetic (pure, runs live offline) ---------------------------
def next_start_seq(last_broker_sequence: int) -> int:
    """Resume offset after seeing `last_broker_sequence`: the NEXT sequence. start_seq is inclusive,
    so advancing by exactly one repeats nothing and skips nothing."""
    return last_broker_sequence + 1
