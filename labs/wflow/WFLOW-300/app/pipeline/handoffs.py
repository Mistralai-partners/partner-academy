"""WFLOW-300 Task 14 (SOLUTION): a coordinator that hands off, plus MCP and a built-in tool.

A single agent should not do everything. A **coordinator** triages the request and, when it
needs deeper expertise, hands the conversation to a **specialist** agent. Three wiring choices
carry this lesson, and each is a real field on `Agent`:

- **handoff** — `handoffs=[specialist]` lets the coordinator transfer control to another agent
  mid-run. The model decides when to hand off; the platform routes the turn to the named agent.
- **MCP tool** — `mcp_clients=[MCPStreamableHTTPConfig(...)]` attaches an external MCP server so
  the coordinator can call tools it does not implement itself (docs search, a ticketing API).
- **built-in tool** — `tools=[WebSearchTool()]` pulls in a platform-provided capability. Built-in
  tools require a `RemoteSession`; a `LocalSession` silently drops them. An activity in the same
  `tools` list is your OWN code exposed as a tool, so the two kinds compose.

Everything here — the handoff graph, the MCP client, the built-in tool, the activity tool — is a
real, introspectable SDK object you build offline. The agent LOOP that actually drives a handoff
or calls the MCP server is platform-only (live model + live MCP endpoint), so the lab checks this
module STRUCTURALLY, the same honest boundary the shipped agent/OBO checks use.

Grounded in: installed mistralai-workflows==3.10.0 introspection — `Agent(handoffs=list[Agent],
mcp_clients=[MCPStreamableHTTPConfig|MCPSSEConfig|MCPStdioConfig], tools=[... WebSearchTool ...])`
(plugins/mistralai/agent.py overrides `handoffs` to accept Agent objects; the built-in tool union
includes `WebSearchTool`); WFLOW-200 agent.py (activity-as-tool + RemoteSession pattern).
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk, WebSearchTool

COORDINATOR_ID = "support-coordinator"
SPECIALIST_ID = "refunds-specialist"

# External MCP server the coordinator can reach for tools it does not implement itself.
DOCS_MCP = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.example.com/mcp",
    name="docs-mcp",
)


@workflows.activity()
async def create_refund(order_id: str, amount: float) -> dict:
    """The specialist's own code, exposed as a tool. A real side effect gets activity retry
    isolation and shows up in the durable history."""
    return {"order_id": order_id, "refunded": amount, "status": "issued"}


def build_specialist() -> workflows_mistralai.Agent:
    """The domain expert the coordinator hands off to."""
    return workflows_mistralai.Agent(
        id=SPECIALIST_ID,
        model="mistral-medium-latest",
        name="refunds-specialist",
        description="Processes refunds once a request is confirmed eligible.",
        instructions="Confirm eligibility, then use create_refund to issue the refund.",
        tools=[create_refund],
    )


def build_coordinator() -> workflows_mistralai.Agent:
    """Triage agent: a built-in tool + an MCP server + a handoff to the specialist."""
    return workflows_mistralai.Agent(
        id=COORDINATOR_ID,
        model="mistral-medium-latest",
        name="support-coordinator",
        description="Triages support requests and escalates refunds to the specialist.",
        instructions=(
            "Search the docs (web + MCP) to answer general questions. "
            "For a refund, hand off to the refunds specialist."
        ),
        tools=[WebSearchTool()],          # built-in tool (needs a RemoteSession)
        mcp_clients=[DOCS_MCP],           # external MCP server
        handoffs=[build_specialist()],    # coordinator -> specialist handoff
    )


@workflows.workflow.define(name="support-handoff-workflow")
class SupportHandoffWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, question: str) -> dict:
        # RemoteSession is required for the built-in tool to survive into the run.
        session = workflows_mistralai.RemoteSession()
        coordinator = build_coordinator()
        outputs = await workflows_mistralai.Runner.run(
            agent=coordinator,
            inputs=question,
            session=session,
        )
        answer = "\n".join(o.text for o in outputs if isinstance(o, TextChunk))
        return {"coordinator_id": COORDINATOR_ID, "answer": answer}
