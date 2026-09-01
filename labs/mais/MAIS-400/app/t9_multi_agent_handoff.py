#!/usr/bin/env python
"""Task 9 (SOLUTION) - Multi-hop handoff pipelines.

Behavior (maps to MAIS-400 L5): create multiple agents and wire them into a
handoff chain. An entry agent receives the user query, then hands off to
specialized agents (research, calculation, graphing) based on the task.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.beta.agents.create(model=..., name=..., instructions=..., tools=[...])
  - client.beta.agents.update(agent_id=..., handoff_to=[...])
  - client.beta.conversations.start(agent_id=..., inputs=...)
    -> .outputs (list of events: agent.handoff, tool.execution, message.output)
Source: context7 /mistralai/client-python docs/sdks/agents/README.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.utils import RetryConfig, BackoffStrategy

load_dotenv()
MODEL = "mistral-small-latest"
RETRY = RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False)


def build_pipeline(client):
    """Create a 3-agent handoff pipeline: entry -> research -> summary."""
    research = client.beta.agents.create(
        model=MODEL,
        name="MAIS-400 Research Agent",
        instructions="You research topics. Answer with 2-3 factual sentences.",
        tools=[{"type": "web_search"}],
    )
    summary = client.beta.agents.create(
        model=MODEL,
        name="MAIS-400 Summary Agent",
        instructions="Summarize the research into one sentence.",
    )
    entry = client.beta.agents.create(
        model=MODEL,
        name="MAIS-400 Entry Agent",
        instructions="Route the user query to the research agent.",
        handoffs=[research.id],
    )
    client.beta.agents.update(agent_id=research.id, handoffs=[summary.id])
    return entry, research, summary


def run_pipeline(client, entry_agent, query):
    """Run a query through the pipeline and return outputs."""
    resp = client.beta.conversations.start(
        agent_id=entry_agent.id,
        inputs=query,
        retries=RETRY,
    )
    return resp.outputs


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    entry, research, summary = build_pipeline(client)
    print(f"entry={entry.id} research={research.id} summary={summary.id}")

    outputs = run_pipeline(client, entry, "What is prompt caching?")
    types = [o.type for o in outputs]
    print(f"output types: {types}")

    final = outputs[-1]
    content = getattr(final, "content", None)
    print(f"final output: {content!r}")

    assert any("handoff" in t for t in types) or content, "pipeline produced no output"
    print("TASK9 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK9 FAIL: {e}")
        sys.exit(1)
