"""WFLOW-200 Task 4 (SOLUTION): wire a simple durable agent inside a workflow.

A durable agent runs the LLM loop (model calls, tool use) INSIDE a workflow, so its state
survives worker crashes and restarts. The wiring has four parts:

- an `@activity` used as a **tool** (side effects get retry isolation and show up in history),
- an `Agent(model=..., name=..., tools=[...])` that declares the model and its tools,
- a **`RemoteSession`** (production-recommended; required if you ever add a built-in tool such
  as `WebSearchTool` — `LocalSession` silently drops built-in tools), and
- `Runner.run(agent=..., inputs=..., session=...)` driving the loop to a final answer.

Grounded in: building-workflows/durable_agents.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk


@workflows.activity()
async def lookup_order_status(order_id: str) -> dict:
    """A workflow activity exposed to the agent as a tool.

    Args:
        order_id: The order to look up.
    """
    return {"order_id": order_id, "status": "shipped"}


def build_session() -> workflows_mistralai.RemoteSession:
    """RemoteSession is the production choice and the only one that keeps built-in tools."""
    return workflows_mistralai.RemoteSession()


def build_support_agent() -> workflows_mistralai.Agent:
    """Declare the agent: a model plus the activity-backed tool it may call."""
    return workflows_mistralai.Agent(
        model="mistral-medium-latest",
        name="support-agent",
        description="Answers customer questions about their orders.",
        instructions="Use the lookup tool to answer questions about order status.",
        tools=[lookup_order_status],
    )


@workflows.workflow.define(name="support-agent-workflow")
class SupportAgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, question: str) -> dict:
        session = build_session()
        agent = build_support_agent()
        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=question,
            session=session,
        )
        answer = "\n".join(o.text for o in outputs if isinstance(o, TextChunk))
        return {"answer": answer}
