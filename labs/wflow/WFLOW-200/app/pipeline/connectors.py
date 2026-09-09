"""WFLOW-200 Task 10 (SOLUTION): call an external service through a Connector slot.

A workflow reaches a third-party API (GitHub, Slack, a CRM) through a **Connector**, not a
hand-rolled HTTP client. The everyday wiring is three parts:

- declare a slot with `connector("...")`,
- list it on the workflow with `@uses_connectors(...)`,
- inject the resolved client into an activity with `Depends(...)` and call the tool through
  `ToolCallClient.call_tool(...)`.

This is the plain Connector slot: the workflow runs as the WORKER, so every execution uses the
worker's (service account's) credentials. That is exactly what you want for a shared integration.
Giving each USER their own connector identity is a different feature (`on_behalf_of=True`) and is
an Advanced (L300) topic, deliberately NOT set here.

Executable boundary (honest): resolving the credential and calling the live tool need the
platform, so the tool call is shown and checked structurally; the slot, the `@uses_connectors`
declaration, and the `Depends` injection are real SDK constructs the check introspects offline.

Grounded in: building-workflows/connectors.md (`connector`, `uses_connectors`, `Depends`,
`ToolCallClient.call_tool`); installed mistralai-workflows==3.10.0
(plugins/mistralai/connectors/). Prior art: WFLOW-300 connectors.py.
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
