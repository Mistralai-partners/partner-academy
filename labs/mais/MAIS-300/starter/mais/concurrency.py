"""Client-side concurrency policy and retry configuration for Mistral chat.

Grounded (mistralai==1.9.11):
  - from mistralai.utils import RetryConfig, BackoffStrategy
      RetryConfig(strategy: str, backoff: BackoffStrategy, retry_connection_errors: bool)
      BackoffStrategy(initial_interval, max_interval, exponent, max_elapsed_time)  # ms
  - retries=<RetryConfig> is accepted by client.chat.complete / complete_async.
  - Concurrency = many client.chat.complete_async(...) coroutines gathered with
    asyncio.gather (see live_concurrency.py).

TASK 2 (Analyze/debug): the retry policy below is wrong on two counts. Fix them.
"""
from mistralai.utils import BackoffStrategy, RetryConfig


def build_retry_config() -> RetryConfig:
    return RetryConfig(
        "backoff",
        BackoffStrategy(
            initial_interval=200,
            max_interval=5000,
            # BUG 1 (Task 2): symptom — under a 429 the client keeps hammering at a
            # near-constant interval. Reason about what interval sequence this
            # `exponent` value produces versus what "exponential" backoff means.
            exponent=1.0,
            max_elapsed_time=30000,
        ),
        retry_connection_errors=True,
    )


def should_retry(status_code: int) -> bool:
    # BUG 2 (Task 2): symptom — a 400/401/404 is retried until timeout, burning
    # quota and hiding the real error. Which HTTP status classes are transient
    # (retrying helps) versus client errors (retrying only wastes quota)?
    return status_code >= 400
