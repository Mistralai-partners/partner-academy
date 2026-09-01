#!/usr/bin/env python
"""Task 1 (SOLUTION) - Build a reliable agent.

Behavior (maps to MAIS-200 B1, FKC Q1/Q2): a reliable agent needs standing
behavior and predictable output. You give it that with two things at build time:
  - `instructions`: the standing behavior it applies to every turn.
  - `completion_args`: safe completion settings. temperature=0 makes replies
    deterministic; max_tokens caps length and cost.

Grounded SDK calls (mistralai==2.9.4, verified live):
  - client.beta.agents.create(model=..., name=..., instructions=...,
        completion_args={"temperature": 0, "max_tokens": ...})  -> Agent (.id,
        .instructions, .completion_args.temperature/.max_tokens)
  - client.beta.conversations.start(agent_id=..., inputs=...)   -> outputs[-1]
        is a "message.output" entry with .content
Source: platform-docs-public public/studio-api/agents/agents-api.md (pinned
        a3e0f0c79c5566128ccb7b90e51cc0e7517297da) + context7 /mistralai/client-python.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "mistral-small-latest"

# The standing behavior the agent must apply on every turn.
INSTRUCTIONS = (
    "You are a support triage assistant. Answer in one short, factual sentence. "
    "If you do not know, say you do not know."
)


def build_agent(client):
    """Create a reliable agent: standing behavior + deterministic, bounded output."""
    return client.beta.agents.create(
        model=MODEL,
        name="MAIS-200 Triage Agent",
        description="Answers support questions reliably and briefly.",
        instructions=INSTRUCTIONS,
        completion_args={"temperature": 0, "max_tokens": 64},
    )


def ask(client, agent, question):
    """Run one turn against the agent and return the final message output entry."""
    resp = client.beta.conversations.start(agent_id=agent.id, inputs=question)
    return resp.outputs[-1]


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    agent = build_agent(client)
    out = ask(client, agent, "What does the acronym SLA stand for?")
    print(f"AGENT id={agent.id}")
    print(f"instructions={agent.instructions!r}")
    print(f"temperature={agent.completion_args.temperature} max_tokens={agent.completion_args.max_tokens}")
    print(f"answer={getattr(out, 'content', None)!r}")

    # Acceptance contract: the agent carries the standing behavior AND the safe
    # completion settings, and a turn produces a real message output.
    assert agent.instructions == INSTRUCTIONS, "agent has no standing behavior (instructions not set)"
    assert agent.completion_args.temperature == 0, "output is not deterministic (temperature != 0)"
    assert agent.completion_args.max_tokens, "output length/cost is unbounded (max_tokens not set)"
    assert out.type == "message.output", f"expected a message output, got {out.type}"
    assert getattr(out, "content", None), "agent returned an empty answer"
    print("TASK1 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK1 FAIL: {e}")
        sys.exit(1)
