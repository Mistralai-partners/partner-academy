"""WFLOW-300 Task 15 (SOLUTION): an interactive, chat-style workflow that waits for input.

Some workflows are not fire-and-forget — they hold a conversation. A support assistant greets the
user, waits for a message, drafts a reply, then waits for a human to confirm before sending. The
primitive that makes this durable is `InteractiveWorkflow.wait_for_input(schema, ...)`:

- the workflow **subclasses `InteractiveWorkflow`** to gain `wait_for_input`;
- inside the entrypoint it calls `await self.wait_for_input(Schema, label=..., timeout=...)`, which
  **suspends at zero cost** until an external client submits input matching `Schema` (a Pydantic
  model). The pending request becomes visible in the workflow's streaming events, which is how a
  chat surface (Vibe Work / Le Chat) renders the prompt and collects the answer;
- a `timeout` turns an unanswered prompt into `asyncio.TimeoutError` instead of an indefinite hang;
- real work between turns (drafting the reply) stays in an `@activity`, so the interactive body
  remains deterministic orchestration.

The actual chat round-trip runs on the platform (an external client submits the input via the
workflow's update handler), so it cannot be driven offline. The lab checks this module
STRUCTURALLY: the InteractiveWorkflow subclassing, the typed `wait_for_input` calls, and the
input schemas are all real SDK constructs you can introspect without a live session — the same
honest boundary the shipped platform-only checks use.

Grounded in: installed mistralai-workflows==3.10.0 introspection — `InteractiveWorkflow` base class
with `wait_for_input(self, schema: type[T], label: str | None = None, timeout=...) -> T`
(core interactive workflow; the class docstring shows the `@workflow.define` + subclass + external
`__submit_input` update pattern). Prior art: approval.py (suspend + handled timeout).
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import InteractiveWorkflow


class ChatTurn(BaseModel):
    """The user's chat message, submitted from the front end as interactive input."""
    message: str


class SendDecision(BaseModel):
    """The human confirmation before the drafted reply is sent."""
    approved: bool


@workflows.activity()
async def draft_reply(message: str) -> str:
    """The real work between turns lives in an activity, not the interactive body."""
    return f"Thanks for your message: {message[:40]!r}. Here is a suggested reply."


@workflows.workflow.define(name="assistant-chat-workflow")
class AssistantChatWorkflow(InteractiveWorkflow):
    def __init__(self) -> None:
        super().__init__()  # InteractiveWorkflow sets up its pending-input bookkeeping
        self.transcript: list[dict] = []

    @workflows.workflow.entrypoint
    async def run(self, opening: str) -> dict:
        self.transcript.append({"role": "assistant", "text": opening})

        # Turn 1: suspend until the user submits a chat message (surfaced in the chat UI).
        turn = await self.wait_for_input(ChatTurn, label="User message")
        self.transcript.append({"role": "user", "text": turn.message})

        # Between turns: the real drafting work is an activity.
        reply = await draft_reply(turn.message)
        self.transcript.append({"role": "assistant", "text": reply})

        # Turn 2: ask for confirmation, but do not wait forever.
        try:
            decision = await self.wait_for_input(
                SendDecision, label="Confirm send", timeout=timedelta(hours=1)
            )
        except asyncio.TimeoutError:
            return {"sent": False, "reason": "timeout", "turns": len(self.transcript)}

        return {"sent": decision.approved, "turns": len(self.transcript)}
