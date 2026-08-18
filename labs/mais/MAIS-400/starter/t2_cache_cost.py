#!/usr/bin/env python
"""Task 2 (STARTER) - Prompt-caching cost analysis and cache-miss diagnosis.

Your job: fix the billing math and the cache-miss diagnosis so they match the
documented prompt-caching rules (billable input = prompt_tokens - cached_tokens;
cached tokens billed at 10%; 64-token cache blocks; prefixes under 64 tokens
can never hit).

STRUCTURAL / OFFLINE CHECK - and why:
  The course teaches `prompt_cache_key` plus reading
  `usage.prompt_tokens_details.cached_tokens`. The pinned SDK (mistralai==1.9.11)
  does NOT expose a `prompt_cache_key` field on the chat request, and automatic
  prefix caching returned cached_tokens=None across repeated large-prefix calls
  in this environment (both verified). A live cache HIT cannot be produced
  deterministically here, so the EXPERT REASONING is checked offline against
  captured/synthetic usage objects. `usage_miss` is the real live shape.
"""
import sys

CACHE_BLOCK = 64

usage_miss = {"prompt_tokens": 741, "cached_tokens": None, "prefix_tokens": 741}
usage_hit = {"prompt_tokens": 1013, "cached_tokens": 960, "prefix_tokens": 1013}
usage_short = {"prompt_tokens": 40, "cached_tokens": None, "prefix_tokens": 40}


def billable_input_tokens(prompt_tokens, cached_tokens):
    # SYMPTOM: every prompt token is billed at full price, so a cache hit never lowers the bill. See tasks.md (Task 2).
    return prompt_tokens


def effective_input_cost_ratio(prompt_tokens, cached_tokens):
    # SYMPTOM: the cache discount is ignored, so the reported cost never drops on a cache hit. See tasks.md (Task 2).
    return 1.0


def diagnose(prompt_tokens, cached_tokens, prefix_tokens):
    # BUG: never applies the 64-token block rule and mislabels a plain miss.
    # TODO: prefix under one block -> "prefix_too_short";
    #       no cached tokens -> "no_hit_check_prefix_stability";
    #       cached tokens not a multiple of 64 -> "invalid_cached_not_block_multiple";
    #       otherwise -> "cache_hit".
    if cached_tokens:
        return "cache_hit"
    return "unknown"


def main():
    assert billable_input_tokens(**{k: usage_hit[k] for k in ("prompt_tokens", "cached_tokens")}) == 53
    assert billable_input_tokens(**{k: usage_miss[k] for k in ("prompt_tokens", "cached_tokens")}) == 741
    ratio_hit = effective_input_cost_ratio(usage_hit["prompt_tokens"], usage_hit["cached_tokens"])
    assert ratio_hit < 0.20, f"expected big savings on a hit, got {ratio_hit:.3f}"
    assert effective_input_cost_ratio(usage_miss["prompt_tokens"], usage_miss["cached_tokens"]) == 1.0
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
