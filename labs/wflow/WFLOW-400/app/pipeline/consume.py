"""WFLOW-400 Task 10 (L5.2): consume an event stream resiliently.

Consuming a workflow's event stream from the SDK client has three failure-aware skills:

- **Resume without gaps.** Read with `client.workflows.events.get_stream_events(workflow_exec_id,
  start_seq)`. After each event, advance `start_seq = event.broker_sequence + 1`. On a dropped
  connection you reconnect from that offset, so nothing repeats and nothing is skipped.
- **Back off on reconnect.** A flapping connection must not hammer the broker, so reconnect delay
  grows exponentially and is capped (e.g. `min(2 ** attempt, 30)`).
- **Detect terminal completion.** Stop when the event type is `WORKFLOW_EXECUTION_COMPLETED`,
  `WORKFLOW_EXECUTION_FAILED`, or `WORKFLOW_EXECUTION_CANCELED`, instead of looping forever.

Executable boundary (honest): the live SSE consume needs the platform (a running execution to
stream from), so `resilient_consume` is shown and source-checked. The three decisions you own —
`next_start_seq`, `is_terminal_status`, `reconnect_backoff` — are pure logic and run live, offline.

Grounded in: building-workflows/consuming_events.md (`get_stream_events(workflow_exec_id,
start_seq)`, `event.broker_sequence + 1`, terminal event types, exponential backoff on
ConnectionError). WFLOW-300 stream_resume.py (resume math).
"""
from __future__ import annotations

import asyncio
from typing import Any

TERMINAL_EVENT_TYPES = frozenset(
    {
        "WORKFLOW_EXECUTION_COMPLETED",
        "WORKFLOW_EXECUTION_FAILED",
        "WORKFLOW_EXECUTION_CANCELED",
    }
)


def next_start_seq(last_broker_sequence: int) -> int:
    """Resume offset after seeing `last_broker_sequence`: the NEXT sequence (advance by one)."""
    return last_broker_sequence + 1


def is_terminal_status(event_type: str) -> bool:
    """True when an event type means the execution has finished (stop consuming)."""
    return event_type in TERMINAL_EVENT_TYPES


def reconnect_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Exponential reconnect backoff for attempt N (0-based), capped so it never runs away."""
    return min(cap, base * (2 ** attempt))


async def resilient_consume(client: Any, execution_id: str, max_retries: int = 10) -> list[dict]:
    """Consume a live event stream, resuming across drops until a terminal event (platform-only).

    `client` is an authenticated `mistralai.client.Mistral`. This reaches the live platform (an
    active execution to stream), so it is not run offline — the lab checks this SHAPE structurally
    and exercises next_start_seq / is_terminal_status / reconnect_backoff live above.
    """
    collected: list[dict] = []
    last_seq = 0
    for attempt in range(max_retries):
        try:
            async for event in client.workflows.events.get_stream_events(
                workflow_exec_id=execution_id,
                start_seq=last_seq,
            ):
                last_seq = next_start_seq(event.broker_sequence)  # advance past this event
                collected.append(event.data)
                if event.data is not None and is_terminal_status(event.data.event_type):
                    return collected
            return collected  # stream ended normally
        except ConnectionError:
            await asyncio.sleep(reconnect_backoff(attempt))  # loop resumes from last_seq
    return collected
