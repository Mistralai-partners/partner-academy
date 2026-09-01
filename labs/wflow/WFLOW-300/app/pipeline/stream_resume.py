"""WFLOW-300 Task 5 (SOLUTION): resilient stream resume with broker_sequence.

Streaming events carry a `broker_sequence` that is ordered, unique, and resume-safe:
reconnecting with `start_seq=N` picks up EXACTLY from sequence N, replaying nothing before it.
So the correct resume offset after seeing an event is `broker_sequence + 1`. Resuming with the
last sequence you saw re-delivers that event (a duplicate); resuming from 0/1 replays the whole
stream. Reconnects must also back off so a flapping connection does not hammer the broker.

This module is PURE LOGIC and runs live, offline. `consume_stream` is a fixed harness that
survives exactly one mid-stream disconnect; the two decisions you own are `next_start_seq`
(the resume offset) and `reconnect_backoff` (the retry delay).

Grounded in: building-workflows/streaming.md ("Sequence Guarantee": ordered / unique / resume-safe;
"Use event.broker_sequence + 1 as the start_seq on reconnect").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    stream: str
    broker_sequence: int
    data: dict


class EventBroker:
    """Stands in for the workflow event stream and enforces the resume-safe guarantee:
    subscribe(start_seq) returns every event with broker_sequence >= start_seq, in order."""

    def __init__(self, n: int, stream: str = "token") -> None:
        self._events = [Event(stream, seq, {"i": seq}) for seq in range(1, n + 1)]

    @property
    def max_seq(self) -> int:
        return self._events[-1].broker_sequence if self._events else 0

    def subscribe(self, start_seq: int) -> list[Event]:
        return [e for e in self._events if e.broker_sequence >= start_seq]


def next_start_seq(last_broker_sequence: int) -> int:
    """Resume offset after seeing `last_broker_sequence`: the NEXT sequence, so nothing repeats."""
    return last_broker_sequence + 1


def reconnect_backoff(attempt: int, base: float = 0.5, cap: float = 8.0) -> float:
    """Exponential backoff for reconnect attempt N (0-based), capped so it never runs away."""
    return min(cap, base * (2 ** attempt))


def consume_stream(broker: EventBroker) -> dict:
    """Fixed harness: consume all events, survive ONE forced mid-stream disconnect, and
    resume with next_start_seq(). Returns the delivered sequence list and backoff schedule.
    Do not edit this function; fix next_start_seq / reconnect_backoff above."""
    delivered: list[int] = []
    backoffs: list[float] = []
    start_seq = 1
    last_seq = 0
    reconnect_attempt = 0
    disconnect_after = 3
    disconnected = False

    while True:
        batch = broker.subscribe(start_seq)
        if not batch:
            break
        forced = False
        for ev in batch:
            if not disconnected and len(delivered) == disconnect_after:
                # Simulate a dropped connection mid-stream, then reconnect.
                disconnected = True
                forced = True
                backoffs.append(reconnect_backoff(reconnect_attempt))
                reconnect_attempt += 1
                start_seq = next_start_seq(last_seq)
                break
            delivered.append(ev.broker_sequence)
            last_seq = ev.broker_sequence
            start_seq = next_start_seq(last_seq)
        if not forced:
            break

    return {"delivered": delivered, "backoffs": backoffs}
