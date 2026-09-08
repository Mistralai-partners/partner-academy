"""WFLOW-300 Task 9 (SOLUTION): call an external tool through a Connector slot.

A workflow reaches a third-party API (GitHub, Slack, a CRM) through a **Connector**, not a
hand-rolled HTTP client. You declare a slot with `connector(...)`, list it on the workflow
with `@uses_connectors(...)`, and inject the resolved client into an activity with
`Depends(...)`. The activity then calls the tool through `ToolCallClient.call_tool(...)`.

This is the plain Connector slot: the workflow runs as the WORKER, so every execution reads
the worker's (service account's) credentials. That is exactly what you want for a shared
integration. Giving each *user* access to their own connector is a different feature
(`on_behalf_of=True`, Task 6) and is deliberately NOT set here.

Grounded in: building-workflows/connectors.md (connector slots, `uses_connectors`, `Depends`,
`ToolCallClient.call_tool`).
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


@workflows.activity(name="list-repo-issues", start_to_close_timeout=timedelta(seconds=30))
async def list_repo_issues(repo: str, gh: ToolCallClient = Depends(github)) -> list[dict]:
    # The Connector client is injected via Depends and resolved from the identity the workflow
    # runs under. With no on_behalf_of, that identity is the WORKER (the service account).
    result = await gh.call_tool(
        tool_name="issue_read",
        arguments={"method": "list", "repo": repo},
    )
    return result


@workflows.workflow.define(name="repo-issue-report")
@uses_connectors(github)
class RepoIssueReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, repo: str) -> list[dict]:
        return await list_repo_issues(repo)
