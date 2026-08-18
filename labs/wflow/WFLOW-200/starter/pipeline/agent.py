"""WFLOW-200 Task 4 (STARTER): wire a simple durable agent inside a workflow.

The agent has no tool and uses the wrong session type. Wire it correctly per tasks.md T4:
give the agent the `lookup_order_status` activity as a tool, and switch the session to the
type the docs prefer for production — the current one silently drops built-in tools, which is
the symptom to reason from.

Grounded in: building-workflows/durable_agents.md.
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk


@workflows.activity()
async def lookup_order_status(order_id: str) -> dict:
    """A workflow activity that should be exposed to the agent as a tool.

    Args:
        order_id: The order to look up.
    """
    return {"order_id": order_id, "status": "shipped"}


def build_session():
    # TODO(T4): this LocalSession silently drops built-in tools — switch to the session type
    # the docs prefer for anything production-facing (decide which; see durable_agents.md).
    return workflows_mistralai.LocalSession()


def build_support_agent() -> workflows_mistralai.Agent:
    # TODO(T4): give the agent the lookup_order_status activity in its tools list.
    return workflows_mistralai.Agent(
        model="mistral-medium-latest",
        name="support-agent",
        description="Answers customer questions about their orders.",
        instructions="Use the lookup tool to answer questions about order status.",
        tools=[],
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
