#!/usr/bin/env python
"""Task 2 (SOLUTION) - Prompt-caching cost analysis and cache-miss diagnosis.

Expert point (maps to FKC Q1 / B1): cached prompt tokens are billed at 10% of
the standard input price, so the billable input is (prompt_tokens - cached_tokens).
Cache blocks are 64 tokens, so cached_tokens is always a multiple of 64 and a
prefix shorter than 64 tokens can never produce a hit. When cached_tokens stays
0, the usual causes are: a prefix under 64 tokens, an unstable prefix (the first
part of the prompt changes each call), or simply the first call for that prefix.

STRUCTURAL / OFFLINE CHECK - and why:
  The course teaches `prompt_cache_key` plus reading
  `usage.prompt_tokens_details.cached_tokens`. The pinned SDK for this lab
  (mistralai==2.9.4) does NOT expose a `prompt_cache_key` field on the chat
  request (verified: it is absent from ChatCompletionRequest.model_fields), and
  automatic prefix caching on this key/model returned cached_tokens=None across
  repeated large-prefix calls (verified live). So a live cache HIT cannot be
  produced deterministically here. We therefore verify the EXPERT REASONING
  offline against captured/synthetic usage objects: the billing math and the
  cache-miss diagnosis. The `usage_miss` fixture below is the real shape returned
  by a live mistral-small-latest call in this environment.
"""
import sys

CACHE_BLOCK = 64

# Real captured shape (live mistral-small-latest, repeated stable prefix): no hit.
usage_miss = {"prompt_tokens": 741, "cached_tokens": None, "prefix_tokens": 741}
# Synthetic hit: long stable prefix served from cache (multiple of 64).
usage_hit = {"prompt_tokens": 1013, "cached_tokens": 960, "prefix_tokens": 1013}
# Short prefix: below one cache block, so a hit is impossible.
usage_short = {"prompt_tokens": 40, "cached_tokens": None, "prefix_tokens": 40}


def billable_input_tokens(prompt_tokens, cached_tokens):
    """Uncached tokens billed at full price; cached omitted from full-price count."""
    return prompt_tokens - (cached_tokens or 0)


def effective_input_cost_ratio(prompt_tokens, cached_tokens):
    """Cost relative to no-cache: uncached@1.0 + cached@0.10, divided by full."""
    cached = cached_tokens or 0
    uncached = prompt_tokens - cached
    return (uncached * 1.0 + cached * 0.10) / prompt_tokens


def diagnose(prompt_tokens, cached_tokens, prefix_tokens):
    """Explain a zero/None cached_tokens using the documented cache rules."""
    if prefix_tokens < CACHE_BLOCK:
        return "prefix_too_short"
    if not cached_tokens:
        return "no_hit_check_prefix_stability"
    if cached_tokens % CACHE_BLOCK != 0:
        return "invalid_cached_not_block_multiple"
    return "cache_hit"


def main():
    # Billing math.
    assert billable_input_tokens(**{k: usage_hit[k] for k in ("prompt_tokens", "cached_tokens")}) == 53
    assert billable_input_tokens(**{k: usage_miss[k] for k in ("prompt_tokens", "cached_tokens")}) == 741
    # Cost ratio: a big cache hit should cut effective input cost well below 1.0.
    ratio_hit = effective_input_cost_ratio(usage_hit["prompt_tokens"], usage_hit["cached_tokens"])
    assert ratio_hit < 0.20, f"expected big savings on a hit, got {ratio_hit:.3f}"
    assert effective_input_cost_ratio(usage_miss["prompt_tokens"], usage_miss["cached_tokens"]) == 1.0
    # Diagnosis.
    assert diagnose(**usage_hit) == "cache_hit"
    assert diagnose(**usage_miss) == "no_hit_check_prefix_stability"
    assert diagnose(**usage_short) == "prefix_too_short"

    print(f"HIT billable={billable_input_tokens(1013, 960)} cost_ratio={ratio_hit:.3f}")
    print(f"MISS diagnosis={diagnose(**usage_miss)} SHORT diagnosis={diagnose(**usage_short)}")
    print("TASK2 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK2 FAIL: {e}")
        sys.exit(1)
