"""WFLOW-400 Task 8 (L4.2): Connector slots, OAuth, on-behalf-of, hardened deployments.

A workflow reaches a third-party API through a **Connector**, not a hand-rolled HTTP client. The
slot wiring is three parts: declare `connector("...")`, list it with `@uses_connectors(...)`, and
inject the resolved client into an activity with `Depends(ToolCallClient)`, which calls the tool via
`call_tool(...)`. A plain slot runs as the WORKER (the service account), which is right for a shared
integration.

The L400 topic the lower tiers deferred is **on-behalf-of (OBO)**: set `on_behalf_of=True` on the
workflow so credentials resolve for the TRIGGERING USER, not the worker. Two consequences follow,
and defending them is the skill:

  1. OBO needs a hardened deployment. The platform rejects an OBO workflow on a non-hardened one,
     because it is minting per-user access and must run in an isolated, audited environment.
  2. Triggering an OBO run may need OAuth. The SDK helper `execute_with_connector_auth_async`
     drives that flow: when auth is required it calls your `on_auth_required(state)` callback, which
     reads `state.auth_url` and sends the user through consent. `ConnectorSlot(connector_name=,
     credentials_name=)` binds which named credential a run uses.

Executable boundary (honest): the slot, `uses_connectors`, `Depends`, `on_behalf_of`, and the OBO
call shape are real SDK constructs checked structurally. The live OAuth round-trip and the live tool
call run on the platform — `run_on_behalf_of` is shown and source-checked, not executed offline.

Grounded in: building-workflows/connectors.md (slots, `uses_connectors`, `Depends`,
`call_tool`, `execute_with_connector_auth_async` + `on_auth_required` reading `state.auth_url`,
`ConnectorSlot`); building-workflows/on_behalf_of.md; managing-workflows-in-production/
hardened_deployments.md. WFLOW-300 obo.py (on_behalf_of contract).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import mistralai.workflows as workflows
from mistralai.workflows import Depends
from mistralai.workflows.plugins.mistralai.connectors import (
    ToolCallClient,
    connector,
    uses_connectors,
)
# Client-side OBO/OAuth helpers. Imported at module level (outside any workflow body), so no
# determinism sandbox applies.
from mistralai.extra.workflows.connector_auth import (
    ConnectorAuthTaskState,
    execute_with_connector_auth_async,
)
from mistralai.extra.workflows.connector_slot import ConnectorSlot

github = connector("github_app")


def resolve_identity(on_behalf_of: bool) -> str:
    """Which identity a Connector call resolves under (offline, pure logic).

    on_behalf_of=True -> the triggering USER's credentials (requires a hardened deployment).
    on_behalf_of=False -> the WORKER's service-account credentials (a shared integration).
    """
    return "triggering_user" if on_behalf_of else "worker_service_account"


@workflows.activity(name="list-user-prs", start_to_close_timeout=timedelta(seconds=30))
async def list_user_prs(repo: str, gh: ToolCallClient = Depends(github)) -> list[dict]:
    # The Connector client is injected via Depends and resolved from the identity the workflow runs
    # under. Under OBO that identity is the TRIGGERING USER, so this reads that user's GitHub.
    result = await gh.call_tool(
        tool_name="pull_request_read",
        arguments={"method": "list", "repo": repo},
    )
    return result


@workflows.workflow.define(name="user-pr-report", on_behalf_of=True)
@uses_connectors(github)
class UserPrReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, repo: str) -> list[dict]:
        return await list_user_prs(repo)


# ---- Client-side OBO trigger with the OAuth callback (live OAuth is platform-only) ----
async def on_auth_required(state: ConnectorAuthTaskState) -> None:
    """Called by the SDK when the OBO run needs the user to authorize. Real UIs open a browser to
    state.auth_url; here we just surface it. If valid credentials already exist, this never fires."""
    if state.auth_url:
        print(f"Open this URL to authorize: {state.auth_url}")


async def run_on_behalf_of(client: Any, repo: str) -> Any:
    """Trigger the OBO workflow with the OAuth flow handled.

    `client` is an authenticated `mistralai.client.Mistral`. This reaches the live platform (auth +
    a hardened, deployed workflow), so it is not run offline — the lab checks this call SHAPE
    structurally, the same honest boundary the shipped platform-only checks use.
    """
    return await execute_with_connector_auth_async(
        client=client,
        workflow_identifier="user-pr-report",
        input_data={"repo": repo},
        connectors=[ConnectorSlot(connector_name="github_app", credentials_name="github-pat-full")],
        on_auth_required=on_auth_required,
    )
