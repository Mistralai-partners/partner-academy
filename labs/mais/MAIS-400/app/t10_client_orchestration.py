#!/usr/bin/env python
"""Task 10 (SOLUTION) - Client-orchestrated control with function results.

Behavior (maps to MAIS-400 L6): run an agent with handoff_execution="client"
so the client controls when and how function calls resolve. The client loop
inspects each output, resolves function calls locally, appends the result,
and continues until the agent emits a final message.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.beta.agents.create(model=..., tools=[function_tool],
        handoff_execution="client")
  - client.beta.conversations.start(agent_id=..., inputs=...)
  - client.beta.conversations.append(
        conversation_id=..., inputs=[FunctionResultEntry(...)])
Source: context7 /mistralai/client-python docs/sdks/conversations/README.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.models import FunctionResultEntry

load_dotenv()
MODEL = "mistral-small-latest"

RATE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_interest_rate",
        "description": "Return the current annual interest rate for a given currency.",
        "parameters": {
            "type": "object",
            "properties": {
                "currency": {"type": "string", "description": "ISO 4217 currency code"}
            },
            "required": ["currency"],
        },
    },
}

RATES = {"USD": "5.25", "EUR": "4.50", "GBP": "5.00"}


def local_tool(name, args):
    """Resolve a function call locally."""
    if name == "get_interest_rate":
        cur = args.get("currency", "USD")
        return RATES.get(cur, "unknown")
    return "unknown tool"


def run_client_loop(client, agent_id, query, max_rounds=10):
    """Drive the agent with client-side function resolution."""
    resp = client.beta.conversations.start(
        agent_id=agent_id,
        inputs=query,
        handoff_execution="client",
    )

    for _ in range(max_rounds):
        last = resp.outputs[-1]
        if last.type != "function.call":
            break
        import json
        args = json.loads(last.arguments) if isinstance(last.arguments, str) else last.arguments
        result = local_tool(last.name, args)
        resp = client.beta.conversations.append(
            conversation_id=resp.conversation_id,
            inputs=[FunctionResultEntry(tool_call_id=last.tool_call_id, result=result)],
        )

    return resp.outputs[-1]


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    agent = client.beta.agents.create(
        model=MODEL,
        name="MAIS-400 Rate Advisor",
        instructions="Use the get_interest_rate tool to answer rate questions. Be brief.",
        tools=[RATE_TOOL],
    )
    print(f"agent={agent.id}")

    final = run_client_loop(client, agent.id, "What is the USD interest rate?")
    content = getattr(final, "content", None)
    print(f"final: type={final.type} content={content!r}")

    assert final.type == "message.output", f"expected message.output, got {final.type}"
    assert content, "agent returned empty content"
    print("TASK10 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK10 FAIL: {e}")
        sys.exit(1)
