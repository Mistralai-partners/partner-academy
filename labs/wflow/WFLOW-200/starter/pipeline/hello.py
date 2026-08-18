"""WFLOW-200 Task 1 (STARTER): define a workflow and its activity.

Goal: a workflow named "hello-world" whose entrypoint runs ONE activity that returns a
greeting. See tasks.md T1 for the acceptance. Grounded in getting-started/your_first_workflow.md.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows


class HelloInput(BaseModel):
    name: str = "World"


# TODO(T1): make `greet` a real activity that RETURNS a greeting containing the name.
# Right now it is a plain function that returns nothing, so no work happens.
async def greet(name: str) -> str:
    return ""


# TODO(T1): register this class as a workflow named "hello-world" with an entrypoint method
# `run` that awaits the greet activity and returns its result.
class HelloWorkflow:
    async def run(self, input: HelloInput) -> str:
        return "not implemented"
