"""WFLOW-300 Task 6 (STARTER): a per-user report that leaks across users.

SYMPTOM: every user who runs this workflow sees the SAME GitHub data, the worker's, instead
of their own. Per-user credential isolation never happens, even though the Connector slot is
declared correctly.

Diagnose which identity this workflow runs under and configure it to act for the triggering
user. Two related facts to note for the write-up (see tasks.md): OBO requires a hardened
deployment, and OBO cannot be combined with schedules. Reference:
../../solution/pipeline/obo.py, building-workflows/on_behalf_of.md,
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
    result = await gh.call_tool(
        tool_name="pull_request_read",
        arguments={"method": "list", "repo": repo},
    )
    return result


# SYMPTOM: this runs under the worker's identity, so it resolves the worker's connectors.
@workflows.workflow.define(name="user-pr-report")
@uses_connectors(github)
class UserPrReportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, repo: str) -> list[dict]:
        return await list_user_prs(repo)
