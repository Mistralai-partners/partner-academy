"""Bounded-retry helper (solution)."""
def backoff_delays(retries: int, base: float = 0.5) -> list[float]:
    return [base * (2 ** i) for i in range(retries)]
