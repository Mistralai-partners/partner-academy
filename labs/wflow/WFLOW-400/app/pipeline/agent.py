"""WFLOW-400 Task 7 (L4.1): a durable agent + safe per-worker MCP credentials.

A durable agent runs the LLM loop (model calls, tool use) INSIDE a workflow, so the whole
conversation is checkpointed and survives a worker crash. Four load-bearing parts:

- an `@activity` promoted to a **tool** — side effects the agent triggers get retry isolation and
  land in the durable history instead of running as opaque, un-replayable model I/O;
- an `Agent(model=..., name=..., tools=[...], id=...)` with a STABLE `id` so the same logical agent
  is addressable across runs and versions;
- a **`RemoteSession`** — the production session type and the only one that keeps built-in tools;
- `Runner.run(agent=..., inputs=..., session=...)` driving the loop to a final answer.

The L400 add is credential safety. An external MCP (Model Context Protocol) server is attached with
`MCPStreamableHTTPConfig(url, name, auth_token_env, header_mapping)`. The config stores the NAMES of
environment variables, never the secret values, so nothing sensitive is serialized into workflow
history. Two worker instances can map the SAME header to DIFFERENT env vars — worker A reads
`NOTION_TOKEN_BOT_A`, worker B reads `NOTION_TOKEN_BOT_B` — giving per-worker identity without any
literal secret in code.

Executable boundary (honest): the agent, its tool, the RemoteSession, and the two MCP configs are
real, introspectable SDK objects, checked structurally. The agent LOOP and the live MCP call run on
the platform against a live model.

Grounded in: WFLOW-200/300 agent patterns (`Agent`/`Runner.run`/`RemoteSession`/activity-as-tool);
building-workflows/durable_agents.md (`MCPStreamableHTTPConfig` with `auth_token_env` +
`header_mapping`, credentials via worker env so secrets never enter history).
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk

AGENT_ID = "docs-assistant-agent"  # stable id: same logical agent across runs / versions

# Per-worker MCP credentials. Only the ENV VAR NAMES live here; the secret values are read from the
# worker's environment at call time and never serialized into workflow history. Two workers map the
# same "Notion-Token" header to different env vars, so each carries its own identity.
MCP_WORKER_A = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.example.com/mcp",
    name="docs-mcp",
    auth_token_env="MCP_ENDPOINT_TOKEN",                    # -> Authorization: Bearer <env value>
    header_mapping={"Notion-Token": "NOTION_TOKEN_BOT_A"},  # header <- whole env value (worker A)
)
MCP_WORKER_B = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.example.com/mcp",
    name="docs-mcp",
    auth_token_env="MCP_ENDPOINT_TOKEN",
    header_mapping={"Notion-Token": "NOTION_TOKEN_BOT_B"},  # same header, different env (worker B)
)


@workflows.activity()
async def lookup_doc(doc_id: str) -> dict:
    """A workflow activity promoted to an agent tool.

    Args:
        doc_id: The document to look up.
    """
    return {"doc_id": doc_id, "title": "Runbook", "status": "current"}


def build_session() -> workflows_mistralai.RemoteSession:
    """RemoteSession is the production choice and the only one that keeps built-in tools."""
    return workflows_mistralai.RemoteSession()


def build_docs_agent() -> workflows_mistralai.Agent:
    """Declare the agent: a model, a stable id, the activity-backed tool, and the MCP server."""
    return workflows_mistralai.Agent(
        id=AGENT_ID,
        model="mistral-medium-latest",
        name="docs-assistant-agent",
        description="Answers documentation questions using an internal doc lookup and an MCP server.",
        instructions="Use lookup_doc for internal docs; use the MCP server for external tools.",
        tools=[lookup_doc],
        mcp_clients=[MCP_WORKER_A],
    )


@workflows.workflow.define(name="docs-agent-workflow")
class DocsAgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, question: str) -> dict:
        session = build_session()
        agent = build_docs_agent()
        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=question,
            session=session,
        )
        answer = "\n".join(o.text for o in outputs if isinstance(o, TextChunk))
        return {"agent_id": AGENT_ID, "answer": answer}
