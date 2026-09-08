"""WFLOW-300 Task 13 (SOLUTION): a durable agent inside a workflow, with an activity as its tool.

A durable agent runs the LLM loop (model calls, tool use) INSIDE a workflow, so the whole
conversation — every tool call and every model turn — is checkpointed and survives a worker
crash or restart. The wiring has four load-bearing parts:

- an `@activity` promoted to a **tool** — side effects the agent triggers get retry isolation and
  land in the durable history instead of running as opaque, un-replayable model I/O;
- an `Agent(model=..., name=..., tools=[...], id=...)` — declaring the model, its tools, and a
  STABLE `id` so the same logical agent is addressable across runs and versions;
- a **`RemoteSession`** — the production session type and the only one that keeps built-in tools
  (a `LocalSession` silently drops them); and
- `Runner.run(agent=..., inputs=..., session=...)` driving the loop to a final answer, which the
  workflow reads back from the returned `TextChunk`s.

The agent LOOP itself (model inference + tool arbitration) executes on the platform against a
live model, so it cannot be exercised offline. The lab checks this module STRUCTURALLY — the
agent, its stable id, the activity-backed tool, and the RemoteSession are all real SDK objects
you can build and introspect without a worker (the shipped precedent: checks that validate agents
structurally rather than running the loop).

Grounded in: WFLOW-200 agent.py (`build_support_agent` / `build_session` / `Runner.run` /
`RemoteSession` / `TextChunk`); installed mistralai-workflows==3.10.0 introspection confirms the
`Agent(..., id=...)` field and the `Runner.run(agent, inputs, session)` signature.
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk

AGENT_ID = "billing-support-agent"  # stable id: same logical agent across runs / versions


@workflows.activity()
async def lookup_invoice(invoice_id: str) -> dict:
    """A workflow activity promoted to an agent tool.

    Args:
        invoice_id: The invoice to look up.
    """
    return {"invoice_id": invoice_id, "status": "paid", "amount": 42.0}


def build_session() -> workflows_mistralai.RemoteSession:
    """RemoteSession is the production choice and the only one that keeps built-in tools."""
    return workflows_mistralai.RemoteSession()


def build_billing_agent() -> workflows_mistralai.Agent:
    """Declare the agent: a model, a stable id, and the activity-backed tool it may call."""
    return workflows_mistralai.Agent(
        id=AGENT_ID,
        model="mistral-medium-latest",
        name="billing-support-agent",
        description="Answers customer questions about their invoices.",
        instructions="Use the lookup_invoice tool to answer questions about an invoice.",
        tools=[lookup_invoice],
    )


@workflows.workflow.define(name="billing-agent-workflow")
class BillingAgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, question: str) -> dict:
        session = build_session()
        agent = build_billing_agent()
        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=question,
            session=session,
        )
        answer = "\n".join(o.text for o in outputs if isinstance(o, TextChunk))
        return {"agent_id": AGENT_ID, "answer": answer}
