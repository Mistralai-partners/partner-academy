#!/usr/bin/env python
"""Task 2 (SOLUTION) - Give an agent a tool and return its result.

Behavior (maps to MAIS-200 B1, FKC Q3): when a conversation asks the model for
data it cannot know, the model emits a `function.call` output. Your job is to run
the real function and feed the answer back with a `FunctionResultEntry` whose
`tool_call_id` MATCHES the call the model made. Without that matching id the model
never receives its result and the conversation cannot finish.

Grounded SDK calls (mistralai==2.9.4, verified live):
  - client.beta.conversations.start(model=..., tools=[...], inputs=...)
        -> outputs[-1].type == "function.call", .name, .arguments, .tool_call_id
  - FunctionResultEntry(tool_call_id=<same id>, result=<str>)   (from mistralai.client.models)
  - client.beta.conversations.append(conversation_id=..., inputs=[entry])
        -> outputs[-1].type == "message.output"
Source: platform-docs-public public/studio-api/agents/handoffs.md +
        conversations/function-calling.md (pinned) + context7.
"""
import json
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.models import FunctionResultEntry

load_dotenv()
MODEL = "mistral-small-latest"

# The "external system" the model cannot see directly.
ORDERS = {"A-100": "shipped", "A-200": "processing"}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Return the status of an order given its id.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The order id."}},
            "required": ["order_id"],
        },
    },
}]


def get_order_status(order_id):
    return json.dumps({"order_id": order_id, "status": ORDERS.get(order_id, "unknown")})


def resolve(client):
    """Start the conversation, run the tool, and return the FINAL response."""
    resp = client.beta.conversations.start(
        model=MODEL,
        tools=TOOLS,
        instructions="Use get_order_status to answer, then state the status plainly.",
        inputs="What is the status of order A-100?",
        completion_args={"temperature": 0, "max_tokens": 128},
    )
    call = resp.outputs[-1]
    if call.type != "function.call":
        return resp  # model answered without the tool; caller will assert on this

    # Execute the real function and return the result with the MATCHING tool_call_id.
    args = json.loads(call.arguments)
    result = get_order_status(**args)
    entry = FunctionResultEntry(tool_call_id=call.tool_call_id, result=result)
    return client.beta.conversations.append(conversation_id=resp.conversation_id, inputs=[entry])


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    final = resolve(client)
    out = final.outputs[-1]
    print(f"final_type={out.type}")
    print(f"answer={getattr(out, 'content', None)!r}")

    # Acceptance contract: the loop closed - the model got its tool result and
    # produced a final answer that reflects the real status ("shipped").
    assert out.type == "message.output", (
        f"the conversation never finished (last output is {out.type}); "
        "the tool result was not returned with a matching tool_call_id"
    )
    content = (getattr(out, "content", "") or "").lower()
    assert "shipped" in content, f"final answer does not reflect the tool result: {content!r}"
    print("TASK2 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK2 FAIL: {e}")
        sys.exit(1)
