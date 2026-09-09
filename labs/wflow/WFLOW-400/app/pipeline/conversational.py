"""WFLOW-400 Task 11 (L5.3): a Vibe-compatible conversational workflow.

A conversational workflow holds a chat: it sends the user an assistant message, suspends for a
reply, and returns an assistant output the Vibe Work surface can render. Four constructs carry the
Vibe contract, and getting the return type right is what makes it publishable:

- the workflow **subclasses `InteractiveWorkflow`** to gain `wait_for_input`;
- `send_assistant_message(...)` displays text to the user (optionally with rich canvas content);
- `await self.wait_for_input(ChatInput(...))` suspends at zero cost until the user submits a
  message; a `timeout` turns an unanswered prompt into `asyncio.TimeoutError` rather than a hang;
- the entrypoint returns `ChatAssistantWorkflowOutput(content=[TextOutput(text=...)])`, the exact
  protocol Vibe web and mobile require. `workflow_display_name` / `workflow_description` are the
  labels Vibe shows.

Executable boundary (honest): the live chat round-trip (an external client submitting input, the
Vibe surface rendering the output) runs on the platform, so this module is checked STRUCTURALLY —
the `InteractiveWorkflow` subclassing, the `ChatAssistantWorkflowOutput` return, and registration
with the Vibe labels are all real SDK constructs you can introspect without a live session.

Grounded in: interacting-with-workflows/conversational_workflows (`InteractiveWorkflow`,
`send_assistant_message`, `wait_for_input(ChatInput())`, `ChatAssistantWorkflowOutput` +
`TextOutput`, `@workflow.define(workflow_display_name=, workflow_description=)`) + publish_in_vibe
(the return contract). WFLOW-300 conversational.py (InteractiveWorkflow + wait_for_input + timeout).
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai


@workflows.activity()
async def draft_reply(message: str) -> str:
    """The real work between turns lives in an activity, not the interactive body."""
    return f"Here is a suggested reply to: {message[:40]!r}"


@workflows.workflow.define(
    name="assistant-vibe-workflow",
    workflow_display_name="Assistant",
    workflow_description="A Vibe-compatible conversational assistant.",
)
class AssistantVibeWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(self) -> workflows_mistralai.ChatAssistantWorkflowOutput:
        # Send the opening turn to the user.
        await workflows_mistralai.send_assistant_message(
            "Hi! Send me a question and I'll draft a reply."
        )

        # Suspend for the user's message, but do not wait forever.
        try:
            user_input = await self.wait_for_input(
                workflows_mistralai.ChatInput(), timeout=timedelta(hours=1)
            )
        except asyncio.TimeoutError:
            return workflows_mistralai.ChatAssistantWorkflowOutput(
                content=[workflows_mistralai.TextOutput(text="Timed out waiting for a message.")]
            )

        message = user_input.message[0].text if user_input.message else ""
        reply = await draft_reply(message)  # real drafting work is an activity

        # Return the exact contract Vibe web + mobile require.
        return workflows_mistralai.ChatAssistantWorkflowOutput(
            content=[workflows_mistralai.TextOutput(text=reply)]
        )
