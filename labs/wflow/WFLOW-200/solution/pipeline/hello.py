"""WFLOW-200 Task 1 (SOLUTION): define a workflow and its activity.

The smallest useful unit of Workflows is a workflow that runs one activity. The workflow
body is deterministic orchestration; the activity is where real work (and side effects) live.
This mirrors the scaffold the CLI generates for `your first workflow`.

- `@workflows.activity()` turns an async function into a retriable unit of work.
- `@workflows.workflow.define(name=...)` registers the class as a workflow.
- `@workflows.workflow.entrypoint` marks the method the platform calls to start a run.
- Workflow input is a Pydantic model, so the payload is validated at the boundary.

Grounded in: getting-started/your_first_workflow.md, building-workflows/activities/basics.md.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows


class HelloInput(BaseModel):
    name: str = "World"


@workflows.activity()
async def greet(name: str) -> str:
    """A single activity that returns a greeting. Real work belongs in activities."""
    return f"Hello, {name}! Welcome to Mistral Workflows."


@workflows.workflow.define(name="hello-world")
class HelloWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: HelloInput) -> str:
        # The body only orchestrates; the greeting is produced inside the activity.
        return await greet(input.name)
