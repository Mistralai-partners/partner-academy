"""A tiny bounded-retry helper used by the VIBE-300 lab.
BUG (intentional): the backoff is computed with the wrong exponent base,
so delays do not grow as documented. Task 2 fixes it.
"""
def backoff_delays(retries: int, base: float = 0.5) -> list[float]:
    # SYMPTOM: delays grow linearly instead of the documented growth. See tasks.md (Task 2).
    return [base * (i + 1) for i in range(retries)]
