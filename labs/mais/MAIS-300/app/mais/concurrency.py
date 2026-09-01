"""Client-side concurrency policy and retry configuration for Mistral chat.

Grounded (mistralai==2.9.4):
  - from mistralai.client.utils import RetryConfig, BackoffStrategy
      RetryConfig(strategy: str, backoff: BackoffStrategy, retry_connection_errors: bool)
      BackoffStrategy(initial_interval, max_interval, exponent, max_elapsed_time)  # ms
  - retries=<RetryConfig> is accepted by client.chat.complete / complete_async.
  - Concurrency = many client.chat.complete_async(...) coroutines gathered with
    asyncio.gather (see live_concurrency.py).

The Analyze skill: an idempotent read like a chat completion should retry only
TRANSIENT failures (429 + 5xx). Retrying a 4xx client error just burns quota and
delays the real error surfacing.
"""
from mistralai.client.utils import BackoffStrategy, RetryConfig


def build_retry_config() -> RetryConfig:
    """Exponential backoff: 200ms -> x2 -> capped at 5s, give up after 30s."""
    return RetryConfig(
        "backoff",
        BackoffStrategy(
            initial_interval=200,
            max_interval=5000,
            exponent=2.0,
            max_elapsed_time=30000,
        ),
        retry_connection_errors=True,
    )


def should_retry(status_code: int) -> bool:
    """Retry only transient failures: 429 (rate limit) and 5xx (server).
    Never retry 4xx client errors (bad request, auth, not found)."""
    return status_code == 429 or 500 <= status_code < 600
