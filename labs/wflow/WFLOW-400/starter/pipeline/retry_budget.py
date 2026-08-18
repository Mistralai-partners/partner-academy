"""WFLOW-400 Task 4 (STARTER): activity retry backoff budget with the wrong growth.

The worker retries a failed activity with EXPONENTIAL backoff (coefficient 2.0, base 1s):
1, 2, 4, 8, ... The code below grows LINEARLY (1, 2, 3, 4), which underestimates worst-case
latency. Fix `backoff_delays` so the delays are exponential.

Reference: ../../solution/pipeline/retry_budget.py, activities/basics.md.
"""
from __future__ import annotations


def backoff_delays(max_attempts: int, base: float = 1.0, coefficient: float = 2.0) -> list[float]:
    n_waits = max(0, max_attempts - 1)
    # BUG: linear growth, ignores the backoff coefficient.
    return [base * (i + 1) for i in range(n_waits)]


def worst_case_backoff(max_attempts: int, base: float = 1.0, coefficient: float = 2.0) -> float:
    return sum(backoff_delays(max_attempts, base, coefficient))
