#!/usr/bin/env python
"""Task 13 (SOLUTION) - Quality gates: regression thresholds on judge scores.

Behavior (maps to MAIS-400 L13): build a pass/fail quality gate from judge
labels. The gate is pure Python (no API call): given a list of labels from a
judge campaign, compute the pass rate and exit non-zero if it falls below
the threshold. This pattern plugs into CI pipelines.

The Observability judges/datasets/campaigns APIs (Enterprise-tier) are
documented here for reference but not called live because they require
Enterprise admin access:
  - client.beta.observability.judges.create(...)
  - client.beta.observability.datasets.create(...)
  - client.beta.observability.campaigns.create(...)

Grounded: context7 /mistralai/client-python docs/sdks/judges/README.md,
          docs/sdks/datasets/README.md, docs/sdks/campaigns/README.md.
"""
import sys


def pass_rate(labels, passing=None):
    """Compute the fraction of labels that are in the passing set."""
    if passing is None:
        passing = {"excellent", "acceptable"}
    if not labels:
        return 0.0
    return sum(1 for l in labels if l in passing) / len(labels)


def quality_gate(rate, threshold=0.90):
    """Return True if the pass rate meets the threshold."""
    return rate >= threshold


def main():
    labels = ["excellent", "acceptable", "poor", "excellent", "acceptable"]
    rate = pass_rate(labels)
    passed = quality_gate(rate, threshold=0.90)
    print(f"labels={labels}")
    print(f"pass_rate={rate:.2f} threshold=0.90 passed={passed}")

    assert rate == 0.8, f"expected pass_rate 0.8, got {rate}"
    assert not passed, "0.8 should NOT pass a 0.90 threshold"

    high_labels = ["excellent"] * 9 + ["acceptable"]
    high_rate = pass_rate(high_labels)
    high_passed = quality_gate(high_rate, threshold=0.90)
    print(f"high_rate={high_rate:.2f} passed={high_passed}")
    assert high_passed, "1.0 should pass a 0.90 threshold"

    print("TASK13 PASS")
    sys.exit(0 if high_passed else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK13 FAIL: {e}")
        sys.exit(1)
