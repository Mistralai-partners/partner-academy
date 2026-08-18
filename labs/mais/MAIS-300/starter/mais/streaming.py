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

TASK 1 (Analyze/debug): this folder has TWO production bugs. Trace them from the
failing tests, then fix them in this file.
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
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(getattr(p, "text", "") or "" for p in content)
    return getattr(content, "text", "") or ""


def fold_events(events) -> StreamResult:
    result = StreamResult()
    for ev in events:
        etype = ev.event
        data = ev.data
        if etype == "message.output.delta":
            # BUG 1 (Task 1): symptom — the user sees only one word, not the full
            # answer. Look at how this line treats each successive delta.
            result.text = _content_text(data.content)
        elif etype in ("tool.execution.started", "function.call.delta"):
            result.tools_seen.append(data.name)
        elif etype == "conversation.response.done":
            result.terminated = True
            break
        # BUG 2 (Task 1): symptom — on a failed turn the caller hangs forever.
        # Compare the events in TERMINAL against the ones this loop actually
        # handles: which terminal event is never acted on?
    return result
