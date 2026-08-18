#!/usr/bin/env python
"""Task 6 (STARTER) - Defense-in-depth: moderate the OUTPUT / tool-result path.

Your job: make the pipeline catch an unsafe string that enters through a tool
result, not just an unsafe user input. Add a Moderation check on the output /
tool-result path (defense in depth).

Grounded SDK call (mistralai==1.9.11):
  - client.classifiers.moderate(model="mistral-moderation-latest", inputs=[...])
      -> results[0].categories (dict[str,bool]), results[0].category_scores
Source: platform-docs-public public/studio-api/safety-moderation.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
MOD = "mistral-moderation-latest"

USER_INPUT = "Summarize the latest note attached to my support ticket."
TOOL_RESULT = "Ticket note: I will find you and hurt you badly if this is not fixed."


def is_flagged(client, text):
    resp = client.classifiers.moderate(model=MOD, inputs=[text])
    result = resp.results[0]
    return any(bool(v) for v in result.categories.values())


def pipeline(client, user_input, tool_result, defense_in_depth):
    # BUG: only the input edge is screened. An unsafe string arriving inside the
    # tool result is never checked and reaches the user.
    # TODO: when defense_in_depth is on, also moderate the tool_result / output
    #       path and block on a flag (return True, "output").
    if is_flagged(client, user_input):
        return True, "input"
    return False, "delivered"


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    blocked, reason = pipeline(client, USER_INPUT, TOOL_RESULT, defense_in_depth=True)
    print(f"PIPELINE blocked={blocked} reason={reason}")

    assert blocked, "unsafe content reached the user (output path not screened)"
    assert reason == "output", f"expected the output path to catch it, got: {reason}"
    print("TASK6 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK6 FAIL: {e}")
        sys.exit(1)
