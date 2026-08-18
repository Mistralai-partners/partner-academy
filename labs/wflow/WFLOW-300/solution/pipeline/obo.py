"""WFLOW-300 Task 6 (SOLUTION): per-user Connector access via on-behalf-of.

A workflow resolves Connector credentials from the identity it runs under. A regular workflow
runs as the WORKER, so every execution reads the worker's (service account's) GitHub. To give
each user access to THEIR OWN connectors, the workflow must run on-behalf-of the triggering
user: set `on_behalf_of=True`. The platform then resolves that user's credentials at runtime.

Two things are true beyond this code and cannot be checked offline (see tasks.md):
  - OBO workflows REQUIRE a hardened deployment; they are rejected on a non-hardened one.
  - `on_behalf_of=True` cannot be combined with `schedules` (a scheduled run has no triggering
    user). The SDK enforces this at decorator time.

Grounded in: building-workflows/on_behalf_of.md, building-workflows/connectors.md,
managing-workflows-in-production/hardened_deployments.md.
"""
from __future__ import annotations

from datetime import timedelta

import mistralai.workflows as workflows
from mistralai.workflows import Depends
from mistralai.workflows.plugins.mistralai.connectors import (
    ToolCallClient,
    connector,
    uses_connectors,
)

github = connector("github_app")


@workflows.activity(name="list-user-prs", start_to_close_timeout=timedelta(seconds=30))
async def list_user_prs(repo: str, gh: ToolCallClient = Depends(github)) -> list[dict]:
    # The Connector client is resolved from the identity the workflow runs under.
    # Under OBO that identity is the TRIGGERING USER, so this reads that user's GitHub.
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
