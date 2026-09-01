"""Task 2 live proof: client-side concurrency + RetryConfig.

Run: uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv \
       python live_concurrency.py
Grounded: many client.chat.complete_async(...) coroutines gathered with
asyncio.gather; retries=<RetryConfig> overrides the client retry policy.
"""
import asyncio
import os
import time

from dotenv import load_dotenv
from mistralai.client import Mistral

from mais.concurrency import build_retry_config, should_retry

load_dotenv("/Users/victor.rojo/source/course-automation/.env")


async def main():
    cfg = build_retry_config()
    prompts = ["Reply with just: A", "Reply with just: B", "Reply with just: C"]
    async with Mistral(api_key=os.environ["MISTRAL_API_KEY"]) as client:
        t0 = time.time()
        tasks = [
            client.chat.complete_async(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": p}],
                max_tokens=5,
                retries=cfg,
            )
            for p in prompts
        ]
        results = await asyncio.gather(*tasks)
        dt = time.time() - t0
    answers = [r.choices[0].message.content.strip() for r in results]
    print(f"{len(answers)} concurrent completions in {dt:.2f}s:", answers)
    print("should_retry(429) =", should_retry(429), "| should_retry(400) =", should_retry(400))
    assert len(answers) == 3
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
