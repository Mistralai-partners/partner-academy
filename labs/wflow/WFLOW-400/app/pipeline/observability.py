"""WFLOW-400 Task 16 (L7.3): read the three trace views + classify an error code.

When a run misbehaves, three trace fetches answer three different questions, and knowing which to
reach for is the skill:

- `get_workflow_execution_trace_summary(execution_id)` — the quick status: total duration, activity
  count, error count. Start here to decide if there is even a problem.
- `get_workflow_execution_trace_otel(execution_id)` — the raw OpenTelemetry spans with timings and
  parent/child links. Use it to find WHERE a run spent its time.
- `get_workflow_execution_trace_events(execution_id, include_internal_events=)` — the chronological
  event list. Use it to see exactly WHAT happened and in what order (and to find reset points).

The second half is turning a failure into an action. A `WorkflowsException` carries a structured
`ErrorCode`; `classify_error_code` maps the code to what an operator should DO — a terminal code
pages a human, a transient one is left to the retry policy, an input error goes back to the caller.

Executable boundary (honest): the error-code classification is pure logic and runs live against the
real `ErrorCode` enum. The three trace fetches need the platform (a real execution id), so
`fetch_all_traces` is shown and source-checked, not run offline.

Grounded in: observability (`get_workflow_execution_trace_otel` / `_summary` / `_events`);
managing-workflows-in-production/reset_workflow.md (trace events + WORKFLOW_TASK_COMPLETED);
WFLOW-200 ops.py (`WorkflowsException` / `ErrorCode` / `is_terminal()`).
"""
from __future__ import annotations

from typing import Any

from mistralai.workflows.exceptions import ErrorCode, WorkflowsException

# Codes that mean "the caller sent something invalid" -> return it to the caller, do not retry.
_INPUT_ERROR_CODES = frozenset(
    {
        ErrorCode.INVALID_ARGUMENTS_ERROR,
        ErrorCode.INVALID_PARAMS_ERROR,
        ErrorCode.INPUT_SIZE_EXCEEDED_ERROR,
    }
)


def classify_error_code(exc: WorkflowsException) -> dict:
    """Map a raised WorkflowsException to an operator action (offline, live SDK enum).

    - terminal code -> page a human; the run will not recover on its own.
    - input error -> return to the caller to fix the request; retrying will not help.
    - otherwise (transient) -> leave it to the platform's retry policy.
    """
    if exc.is_terminal():
        action = "page_operator"
    elif exc.code in _INPUT_ERROR_CODES:
        action = "return_to_caller"
    else:
        action = "let_retry_policy_recover"
    return {
        "code": exc.code.value if exc.code else None,
        "terminal": exc.is_terminal(),
        "action": action,
    }


def fetch_all_traces(client: Any, execution_id: str) -> dict:
    """Pull all three trace views for one execution (live fetches are platform-only).

    `client` is an authenticated `mistralai.client.Mistral`. These reach the live platform (a real
    execution to trace), so they are not run offline — the lab checks the three call SHAPES and the
    error-code classification structurally/live.
    """
    executions = client.workflows.executions
    return {
        "summary": executions.get_workflow_execution_trace_summary(execution_id=execution_id),
        "otel": executions.get_workflow_execution_trace_otel(execution_id=execution_id),
        "events": executions.get_workflow_execution_trace_events(
            execution_id=execution_id, include_internal_events=True
        ),
    }
