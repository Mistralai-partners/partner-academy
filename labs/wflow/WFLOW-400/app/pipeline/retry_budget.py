"""WFLOW-400 Task 4 (SOLUTION): activity retry backoff budget.

A failed activity is retried up to `retry_policy_max_attempts` with EXPONENTIAL backoff
governed by `retry_policy_backoff_coefficient` (default 2.0), starting from a 1-second base
(see activities/basics.md and the worker defaults: max_attempts=3, backoff_coefficient=2.0).

There is one wait BETWEEN each pair of attempts, so N attempts produce N-1 waits.
Computing this budget lets you reason about worst-case latency before failure propagates
to the workflow.
"""
from __future__ import annotations


def backoff_delays(max_attempts: int, base: float = 1.0, coefficient: float = 2.0) -> list[float]:
    """Wait schedule between attempts: base * coefficient**i for i in 0..(max_attempts-2)."""
    n_waits = max(0, max_attempts - 1)
    return [base * (coefficient ** i) for i in range(n_waits)]


def worst_case_backoff(max_attempts: int, base: float = 1.0, coefficient: float = 2.0) -> float:
    """Total worst-case delay added by retries before the failure surfaces."""
    return sum(backoff_delays(max_attempts, base, coefficient))
