"""WFLOW-300 Task 5 (STARTER): a stream consumer that mishandles reconnects.

SYMPTOMS after a mid-stream disconnect:
  - An event is delivered twice (a duplicate appears in the output).
  - Reconnects fire back-to-back with no growing delay, hammering the broker.

`consume_stream` is a fixed harness and must not be edited. Diagnose the resume offset and the
retry delay: the two functions below decide where the stream picks up after a drop and how long
to wait before reconnecting. Reference: ../../solution/pipeline/stream_resume.py,
building-workflows/streaming.md ("Sequence Guarantee").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    stream: str
    broker_sequence: int
    data: dict


class EventBroker:
    """subscribe(start_seq) returns every event with broker_sequence >= start_seq, in order."""

    def __init__(self, n: int, stream: str = "token") -> None:
        self._events = [Event(stream, seq, {"i": seq}) for seq in range(1, n + 1)]

    @property
    def max_seq(self) -> int:
        return self._events[-1].broker_sequence if self._events else 0

    def subscribe(self, start_seq: int) -> list[Event]:
        return [e for e in self._events if e.broker_sequence >= start_seq]


def next_start_seq(last_broker_sequence: int) -> int:
    # SYMPTOM: resuming here re-delivers the last event we already saw.
    return last_broker_sequence


def reconnect_backoff(attempt: int, base: float = 0.5, cap: float = 8.0) -> float:
    # SYMPTOM: a constant delay means reconnects never back off under a flapping connection.
    return base


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
