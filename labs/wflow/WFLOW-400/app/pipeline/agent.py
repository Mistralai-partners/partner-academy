"""WFLOW-400 Task 7 (L4.1): a durable agent + safe per-worker MCP credentials.

A durable agent runs the LLM loop (model calls, tool use) INSIDE a workflow, so the whole
conversation is checkpointed and survives a worker crash. Four load-bearing parts:

- an `@activity` promoted to a **tool**, so side effects the agent triggers get retry isolation and
  land in the durable history instead of running as opaque, un-replayable model I/O;
- an `Agent(model=..., name=..., tools=[...], mcp_clients=[...])` built CREATE-FRESH (NO hardcoded
  id), so `RemoteSession` creates a new remote agent per run instead of 404-ing on a made-up id;
- a **`RemoteSession`**, the production session type and the only one that keeps built-in tools;
- `Runner.run(agent=..., inputs=..., session=...)` driving the loop to a final answer.

Agent identity, and why create-fresh is the default (design A). The platform ASSIGNS the agent id on
create; `CreateAgentRequest` has no id field. Hand `Agent` a human-readable string id and the session
takes its "already exists" branch, calling `update_agent(agent_id=...)`, which 404s because that id
was never created (surfaced as agent_execution_error 500). So the runnable default OMITS `id`: the
session runs its create branch and writes the platform-assigned id back onto the local object.

Production optimization (design B: create-once, then reuse). To avoid minting a new remote agent on
every run: create the agent once WITHOUT an id, read the platform-assigned `mistral_agent.id` the
session wrote back (returned here as the workflow's `agent_id`), persist it (workflow input, config,
or a small store), then pass that REAL id back on later runs so the session takes its update branch
and reuses the same agent. You cannot pick a human-readable id; the platform assigns it, so only a
real assigned id is safe to pass back.

The L400 add is credential safety. An external MCP (Model Context Protocol, a standard for exposing
tools to models over HTTP) server is attached with `MCPStreamableHTTPConfig`. The runnable workflow
points at an anonymous Context7 server, so a cold run works with zero secrets. The two `MCP_WORKER_*`
configs are the credential-safety EXAMPLE: they store the NAMES of env vars (`auth_token_env`), never
secret values, so nothing sensitive is serialized into workflow history, and each worker reads a
DIFFERENT key env var, giving per-worker identity without any literal secret in code.

Executable boundary (honest): create-fresh runs live. The RemoteSession creates a real remote agent,
the loop runs on the platform against a real model, the `lookup_doc` tool executes as a durable
activity, and the anonymous Context7 MCP resolves for real. The two per-worker-key MCP configs are
real, introspectable SDK objects checked structurally; they are the credential PATTERN, not the
runnable path (set `CONTEXT7_KEY_BOT_A` / `CONTEXT7_KEY_BOT_B` and swap one in to run a live
per-identity call).

Grounded in: WFLOW-200/300 agent patterns (`Agent`/`Runner.run`/`RemoteSession`/activity-as-tool);
mistralai-workflows `RemoteSession._create_or_update_agent` (create when no id, update when id set,
then `agent.id = mistral_agent.id`); building-workflows durable-agents guidance
(`MCPStreamableHTTPConfig` with `auth_token_env`, credentials via worker env so secrets never enter
history).
"""
from __future__ import annotations

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk

# The MCP server the WORKFLOW actually uses. Context7 is ONE EXAMPLE of a real, resolvable MCP
# server; it works anonymously at a public rate limit, so a cold run needs no credentials. Swap in
# any other streamable-HTTP MCP server the same way, for example:
#   - GitHub remote MCP:  MCPStreamableHTTPConfig(url="https://api.githubcopilot.com/mcp/", ...)  (OAuth)
#   - a self-hosted Notion MCP over HTTP with a bearer token (auth_token_env=...)
#   - a local reference `fetch` / `filesystem` MCP server exposed over streamable HTTP
CONTEXT7_MCP = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.context7.com/mcp",
    name="context7",
)

# EXAMPLE (not the runnable path): per-worker MCP credentials for lesson objective 3. Only the ENV
# VAR NAMES live here; the secret values are read from each worker's environment at call time and are
# never serialized into workflow history. Both workers point at the SAME Context7 url but read
# DIFFERENT key env vars, so each carries its own identity. To run a live per-identity call, set the
# named env vars and pass one of these to `build_docs_agent(mcp=...)`.
MCP_WORKER_A = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.context7.com/mcp",
    name="context7",
    auth_token_env="CONTEXT7_KEY_BOT_A",  # worker A resolves its key from this env var at runtime
)
MCP_WORKER_B = workflows_mistralai.MCPStreamableHTTPConfig(
    url="https://mcp.context7.com/mcp",
    name="context7",
    auth_token_env="CONTEXT7_KEY_BOT_B",  # worker B: same server, different identity via a different env var
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


def build_docs_agent(
    mcp: workflows_mistralai.MCPStreamableHTTPConfig | None = None,
) -> workflows_mistralai.Agent:
    """Declare the agent CREATE-FRESH: a model, the activity-backed tool, and one MCP server.

    No `id` is set, so `RemoteSession` creates a new remote agent per run and writes the
    platform-assigned id back onto this object (read it after `Runner.run` for design B reuse). The
    default MCP server is the anonymous Context7 config so a cold run works; pass `mcp=MCP_WORKER_A`
    (or `MCP_WORKER_B`) to exercise the per-worker credential pattern.
    """
    return workflows_mistralai.Agent(
        model="mistral-medium-latest",
        name="docs-assistant-agent",
        description="Answers documentation questions using an internal doc lookup and an MCP server.",
        instructions="Use lookup_doc for internal docs; use the MCP server for external tools.",
        tools=[lookup_doc],
        mcp_clients=[mcp or CONTEXT7_MCP],
    )


@workflows.workflow.define(name="docs-agent-workflow")
class DocsAgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, question: str) -> dict:
        session = build_session()
        agent = build_docs_agent()  # create-fresh: no id passed in
        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=question,
            session=session,
        )
        answer = "\n".join(o.text for o in outputs if isinstance(o, TextChunk))
        # After the run, `agent.id` holds the platform-assigned id the session wrote back. Persist
        # this value and pass it to a future `Agent(id=...)` to reuse the same remote agent (design B).
        return {"agent_id": agent.id, "answer": answer}
