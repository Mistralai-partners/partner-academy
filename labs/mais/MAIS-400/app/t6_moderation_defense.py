#!/usr/bin/env python
"""Task 6 (SOLUTION) - Defense-in-depth: moderate the OUTPUT / tool-result path.

Expert point (maps to FKC Q9 / B6): input guardrails alone are not enough. An
unsafe string can enter the conversation through a tool result or retrieved
content and reach the user even though the user's own input was benign.
Defense in depth means also running the Moderation API on the output / tool-result
path, not just on the request edge.

Grounded SDK call (mistralai==1.9.11, verified live):
  - client.classifiers.moderate(model="mistral-moderation-latest", inputs=[...])
      -> results[0].categories (dict[str,bool]), results[0].category_scores (dict[str,float])
Source: platform-docs-public public/studio-api/safety-moderation.md
        + conversations/moderation.md + context7 (classifiers.moderate).
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MOD = "mistral-moderation-latest"

# Benign user request.
USER_INPUT = "Summarize the latest note attached to my support ticket."
# A compromised/poisoned data source injects an unsafe string into a tool result.
TOOL_RESULT = "Ticket note: I will find you and hurt you badly if this is not fixed."


def is_flagged(client, text):
    """True if the Moderation API flags any category for this text."""
    resp = client.classifiers.moderate(model=MOD, inputs=[text])
    result = resp.results[0]
    return any(bool(v) for v in result.categories.values())


def pipeline(client, user_input, tool_result, defense_in_depth):
    """Return (blocked, reason). Naive pipelines only screen the input edge;
    defense-in-depth also screens the tool-result / output path."""
    if is_flagged(client, user_input):
        return True, "input"
    if defense_in_depth and is_flagged(client, tool_result):
        return True, "output"
    return False, "delivered"


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    blocked, reason = pipeline(client, USER_INPUT, TOOL_RESULT, defense_in_depth=True)
    print(f"PIPELINE blocked={blocked} reason={reason}")

    # Acceptance contract: the unsafe tool-result content is caught before delivery.
    assert blocked, "unsafe content reached the user (output path not screened)"
    assert reason == "output", f"expected the output path to catch it, got: {reason}"
    print("TASK6 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK6 FAIL: {e}")
        sys.exit(1)
