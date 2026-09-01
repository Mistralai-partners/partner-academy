"""Fold a Mistral conversations event stream into a terminal final state.

Grounded (mistralai==1.9.11): client.beta.conversations.start_stream(...) returns
an EventStream of ConversationEvents. Each item has:
  - .event : the event-type string, one of
      conversation.response.started / message.output.delta /
      tool.execution.started / tool.execution.delta / tool.execution.done /
      function.call.delta / agent.handoff.started / agent.handoff.done /
      conversation.response.done / conversation.response.error
  - .data  : the typed event payload (MessageOutputEvent, ResponseDoneEvent,
             ResponseErrorEvent, FunctionCallEvent, ToolExecution*Event, ...)

The Analyze skill: a client must ACCUMULATE message deltas and TERMINATE on the
two terminal events (done AND error). Forgetting the error branch is the classic
"the UI hangs on a failed turn" production bug.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional

TERMINAL = {"conversation.response.done", "conversation.response.error"}


@dataclass
class StreamResult:
    text: str = ""
    tools_seen: List[str] = field(default_factory=list)
    terminated: bool = False
    error: Optional[str] = None


def _content_text(content: Any) -> str:
    """message.output.delta content is a text string for text turns; be defensive
    if the SDK hands back a list of content chunks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(getattr(p, "text", "") or "" for p in content)
    return getattr(content, "text", "") or ""


def fold_events(events) -> StreamResult:
    """Accumulate a conversations event stream into a StreamResult.

    Terminates (breaks) on BOTH conversation.response.done and
    conversation.response.error so the caller never hangs.
    """
    result = StreamResult()
    for ev in events:
        etype = ev.event
        data = ev.data
        if etype == "message.output.delta":
            result.text += _content_text(data.content)
        elif etype in ("tool.execution.started", "function.call.delta"):
            result.tools_seen.append(data.name)
        elif etype == "conversation.response.error":
            result.error = data.message
            result.terminated = True
            break
        elif etype == "conversation.response.done":
            result.terminated = True
            break
    return result
