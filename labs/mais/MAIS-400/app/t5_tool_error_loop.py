#!/usr/bin/env python
"""Task 5 (SOLUTION) - Resilient function-result error loops.

Expert point (maps to FKC Q8 / B5): in a tool loop, when a lookup cannot find
the requested record, the resilient behavior is to return a STRUCTURED error
result back into the conversation as the tool message, so the model can recover
and produce a final answer. Raising (or leaving the tool call unanswered) breaks
the loop and the integration.

Grounded SDK calls (mistralai==1.9.11, verified live):
  - client.chat.complete(model=..., messages=..., tools=..., tool_choice=...)
      -> choices[0].message.tool_calls[i].function.{name, arguments}, .id
  - append {"role": "tool", "name": ..., "content": ..., "tool_call_id": ...}
Source: platform-docs-public public/studio-api/conversations/function-calling.md.
"""
import json
import os
import sys

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
MODEL = "mistral-small-latest"

INVENTORY = {"AB-1": 5, "AB-2": 0}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_inventory",
        "description": "Return stock level for a SKU.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string", "description": "The SKU code."}},
            "required": ["sku"],
        },
    },
}]


def get_inventory(sku):
    """RESILIENT: unknown SKU returns a structured error result, never raises."""
    if sku in INVENTORY:
        return json.dumps({"sku": sku, "quantity": INVENTORY[sku]})
    return json.dumps({"error": "sku_not_found", "sku": sku})


def run(client, user_msg, max_turns=5):
    messages = [
        {"role": "system", "content": "You answer inventory questions using the tool."},
        {"role": "user", "content": user_msg},
    ]
    resp = client.chat.complete(model=MODEL, messages=messages, tools=TOOLS,
                                tool_choice="any", max_tokens=128, temperature=0)
    for _ in range(max_turns):
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return resp.choices[0].finish_reason, msg.content
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = get_inventory(**args)
            messages.append({"role": "tool", "name": call.function.name,
                             "content": result, "tool_call_id": call.id})
        resp = client.chat.complete(model=MODEL, messages=messages, tools=TOOLS,
                                    max_tokens=128, temperature=0)
    raise RuntimeError("loop did not converge within max_turns")


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    # Ask about a SKU that does NOT exist -> the loop must still finish cleanly.
    finish, content = run(client, "How many units of SKU ZZ-9 are in stock?")
    print(f"FINISH={finish} CONTENT={content!r}")

    # Acceptance contract: loop completed with a final answer, no crash.
    assert finish == "stop", f"loop did not reach a final answer (finish={finish})"
    assert content and content.strip(), "final answer was empty"
    print("TASK5 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK5 FAIL: {e}")
        sys.exit(1)
