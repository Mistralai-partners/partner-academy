"""WFLOW-200 acceptance checks. Run via verify/check.sh <starter|solution>.

Deterministic, objective checks for all five L200 build tasks. L200 is Apply: the learner
builds the everyday pieces (a workflow + activity, activity configuration, the three
interaction primitives, a durable agent, offloadable payloads) and each check confirms the
piece is wired correctly.

Where the durable orchestrator would be required (a real run, a live agent turn), we verify
the contract the SDK CAN enforce offline: structural validation through the REAL
mistralai-workflows SDK (registration / introspection / activity metadata), plus pure logic
and Pydantic models that run live. Each check's message says which mode it used. Nothing
fakes a pass.

Prints PASS/FAIL per check; exit code = number of failures.
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TARGET = sys.argv[1] if len(sys.argv) > 1 else "."
if TARGET == ".":
    TARGET_DIR = HERE
else:
    TARGET_DIR = os.path.join(os.path.dirname(HERE), TARGET)
sys.path.insert(0, TARGET_DIR)  # so `import pipeline.*` resolves to the target tree

_pass = 0
_fail = 0


def ok(msg: str) -> None:
    global _pass
    _pass += 1
    print(f"  PASS: {msg}")


def no(msg: str) -> None:
    global _fail
    _fail += 1
    print(f"  FAIL: {msg}")


def check(name: str, fn) -> None:
    try:
        good, detail = fn()
        (ok if good else no)(f"{name} - {detail}")
    except Exception as exc:  # noqa: BLE001
        no(f"{name} - raised {type(exc).__name__}: {exc}")


def _fresh(modname: str):
    full = f"pipeline.{modname}"
    if full in sys.modules:
        del sys.modules[full]
    return importlib.import_module(full)


def _module_source(modname: str) -> str:
    return open(os.path.join(TARGET_DIR, "pipeline", f"{modname}.py")).read()


def _is_activity(fn) -> bool:
    return hasattr(fn, "__temporal_activity_definition")


# ---- Task 1: define a workflow + activity (LIVE logic + SDK registration) ------------
def t1():
    import mistralai.workflows as workflows
    mod = _fresh("hello")

    if not _is_activity(mod.greet):
        return (False, "greet is not an @activity - decorate it with @workflows.activity()")
    out = asyncio.run(mod.greet("World"))
    if "Hello" not in out or "World" not in out:
        return (False, f"greet must return a greeting containing the name; got {out!r} (live)")

    spec = workflows.get_workflow_definition(mod.HelloWorkflow)
    if spec.name != "hello-world":
        return (False, f"workflow must register as 'hello-world', got {spec.name!r}")

    run_src = inspect.getsource(mod.HelloWorkflow.run)
    if "greet" not in run_src:
        return (False, "the entrypoint must call the greet activity, not build the string inline")
    return (True, "greet runs live; HelloWorkflow registers and its entrypoint calls it (live + SDK)")


# ---- Task 2: configure timeout + retries + heartbeat (SDK metadata + LIVE) -----------
def t2():
    import mistralai.workflows as workflows
    mod = _fresh("activity_config")

    params = getattr(mod.fetch_quote, "__wf_activity_params__", None)
    if params is None:
        return (False, "fetch_quote carries no activity params - is it still an @activity?")

    if not params.get("retry_policy_max_attempts") or params["retry_policy_max_attempts"] < 2:
        return (False, "set retry_policy_max_attempts >= 2 so a transient failure is retried")
    if not params.get("retry_policy_backoff_coefficient"):
        return (False, "set retry_policy_backoff_coefficient (e.g. 2.0) for exponential backoff")
    if not params.get("heartbeat_timeout_seconds"):
        return (False, "set heartbeat_timeout so a stalled long call is detected before the timeout")

    # start_to_close default is 300s, so metadata can't tell explicit from default: check source.
    src = _module_source("activity_config")
    if "start_to_close_timeout=" not in src:
        return (False, "set an explicit start_to_close_timeout on the activity")
    if "activity_heartbeat(" not in src:
        return (False, "a long activity must checkpoint with workflows.activity_heartbeat(...)")

    result = asyncio.run(mod.fetch_quote("AAPL"))
    if result.get("symbol") != "AAPL":
        return (False, f"fetch_quote should return the symbol it was called with; got {result} (live)")

    spec = workflows.get_workflow_definition(mod.QuoteWorkflow)
    if spec.name != "quote-workflow":
        return (False, f"workflow must register as 'quote-workflow', got {spec.name!r}")
    return (True, "timeout+retry+heartbeat set (SDK metadata); activity runs (live); workflow registers")


# ---- Task 3: signal + query + update (structural via real SDK introspection) ---------
def t3():
    import mistralai.workflows as workflows
    mod = _fresh("interactions")
    spec = workflows.get_workflow_definition(mod.OrderWorkflow)

    if not any(s.name == "cancel_order" for s in spec.signals):
        return (False, "no 'cancel_order' signal registered - the workflow cannot be told to cancel")
    if not any(q.name == "get_status" for q in spec.queries):
        return (False, "no 'get_status' query registered - state cannot be read from outside")
    upd = [u for u in spec.updates if u.name == "add_item"]
    if not upd:
        return (False, "no 'add_item' update registered - cannot add an item and get the total back")

    add_src = inspect.getsource(mod.OrderWorkflow.add_item)
    if "price_item" not in add_src:
        return (False, "the add_item update must run the price_item activity (updates may run activities)")

    if asyncio.run(mod.price_item("abc")) != 3.0:
        return (False, "price_item activity should return a deterministic price (live)")
    return (True, "cancel_order signal, get_status query, add_item update all registered (SDK) + activity live")


# ---- Task 4: wire a simple durable agent (structural; Agent built offline) -----------
def t4():
    import mistralai.workflows as workflows
    mod = _fresh("agent")

    if not _is_activity(mod.lookup_order_status):
        return (False, "lookup_order_status must be an @activity to be used as a tool")

    agent = mod.build_support_agent()
    if not any(t is mod.lookup_order_status for t in getattr(agent, "tools", []) or []):
        return (False, "the agent has no tool - add lookup_order_status to the agent's tools list")
    if not isinstance(getattr(agent, "model", None), str) or not agent.model:
        return (False, "the agent must declare a model")

    session = mod.build_session()
    if type(session).__name__ != "RemoteSession":
        return (False, "use RemoteSession (LocalSession silently drops built-in tools)")

    spec = workflows.get_workflow_definition(mod.SupportAgentWorkflow)
    if spec.name != "support-agent-workflow":
        return (False, f"workflow must register as 'support-agent-workflow', got {spec.name!r}")

    run_src = inspect.getsource(mod.SupportAgentWorkflow.run)
    if "Runner.run" not in run_src:
        return (False, "the entrypoint must drive the agent with Runner.run(...)")
    # Structural-only boundary: Runner.run needs the live Agents API and is NOT executed here.
    return (True, "agent has the activity tool + a model + RemoteSession; workflow registers (structural)")


# ---- Task 5: payload basics - offloadable field (LIVE model round-trip + source) -----
def t5():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.encoding.fields_offloader import OffloadableModel
    mod = _fresh("payload")

    if not issubclass(mod.TranscriptionPayload, OffloadableModel):
        return (False, "TranscriptionPayload must subclass OffloadableModel to offload large fields")

    inst = mod.TranscriptionPayload(audio_id="a1")
    if not hasattr(inst.transcript, "get_value"):
        return (False, "the transcript field must be an OffloadableField, not a plain str")

    out = asyncio.run(mod.transcribe(mod.TranscriptionPayload(audio_id="a1")))
    if not out.transcript.get_value():
        return (False, "transcribe must return the transcript in an OffloadableField (live)")

    run_src = inspect.getsource(mod.TranscribeWorkflow.run)
    if ".get_value(" in run_src:
        return (False, "do NOT call .get_value() in the workflow body - pass the field through as-is")

    spec = workflows.get_workflow_definition(mod.TranscribeWorkflow)
    if spec.name != "transcribe-workflow":
        return (False, f"workflow must register as 'transcribe-workflow', got {spec.name!r}")
    return (True, "offloadable model round-trips live; workflow passes the field through (live + source)")


# ---- Task 6: activity flavors + dependency injection (structural via real SDK) --------
def t6():
    import mistralai.workflows as workflows
    mod = _fresh("flavors")

    for name in ("validate_row", "normalize_field", "lookup_in_cache", "persist_record"):
        if not _is_activity(getattr(mod, name)):
            return (False, f"{name} must be an @activity")

    src = _module_source("flavors")
    if "run_activities_locally(" not in src:
        return (False, "use run_activities_locally() (sync ctx mgr) for the local flavor")
    if "run_sticky_worker_session(" not in src:
        return (False, "use run_sticky_worker_session() (async ctx mgr) for the sticky flavor")
    if "sticky_to_worker=True" not in src:
        return (False, "mark the sticky activity with sticky_to_worker=True")
    if "Depends(" not in src:
        return (False, "inject a dependency with Depends(provider)")

    spec = workflows.get_workflow_definition(mod.ImportWorkflow)
    if spec.name != "import-workflow":
        return (False, f"workflow must register as 'import-workflow', got {spec.name!r}")
    return (True, "local + sticky flavors + Depends present (source); ImportWorkflow registers (SDK)")


# ---- Task 7: workflow determinism (LIVE activity + source lint + SDK) ------------------
def t7():
    import mistralai.workflows as workflows
    mod = _fresh("determinism")

    if not _is_activity(mod.fetch_exchange_rate):
        return (False, "fetch_exchange_rate must be an @activity (I/O belongs in activities)")
    if asyncio.run(mod.fetch_exchange_rate("GBPUSD")) != 1.25:
        return (False, "fetch_exchange_rate should return a deterministic rate (live)")

    body = inspect.getsource(mod.FxReportWorkflow.run)
    for good in ("workflow.now(", "workflow.uuid4(", "workflow.random("):
        if good not in body:
            return (False, f"the workflow body must use {good}...) for determinism")
    for bad in ("datetime.now(", "uuid.uuid4(", "random.random("):
        if bad in body:
            return (False, f"remove the non-deterministic {bad}...) from the workflow body")

    spec = workflows.get_workflow_definition(mod.FxReportWorkflow)
    if spec.name != "fx-report-workflow":
        return (False, f"workflow must register as 'fx-report-workflow', got {spec.name!r}")
    workflows.get_workflow_definition(mod.EscapeHatchWorkflow)  # registers (escape hatch)
    return (True, "activity runs (live); body uses deterministic APIs only (source); registers (SDK)")


# ---- Task 8: streaming publish + resume (LIVE resume math + structural publish) --------
def t8():
    import mistralai.workflows as workflows
    mod = _fresh("streaming")

    if not _is_activity(mod.stream_tokens):
        return (False, "stream_tokens must be an @activity to publish from a workflow")

    src = _module_source("streaming")
    if "workflows.task(" not in src:
        return (False, "publish progress with the workflows.task(...) context manager")
    if "update_state(" not in src:
        return (False, "emit progress events with task.update_state(...)")

    # The resume rule is pure logic and runs live: advance by exactly one, never repeat.
    if mod.next_start_seq(3) != 4:
        return (False, "next_start_seq must be last broker_sequence + 1")
    if not (mod.reconnect_backoff(0) < mod.reconnect_backoff(2)):
        return (False, "reconnect_backoff must grow with the attempt number")

    spec = workflows.get_workflow_definition(mod.StreamingWorkflow)
    if spec.name != "streaming-workflow":
        return (False, f"workflow must register as 'streaming-workflow', got {spec.name!r}")
    return (True, "resume offset = last+1 (live); publish via task().update_state (source); registers")


# ---- Task 9: child workflow + continue-as-new + schedule (LIVE math + structural) ------
def t9():
    import mistralai.workflows as workflows
    from mistralai.workflows.models import ScheduleDefinition
    mod = _fresh("child_continue")

    # Carry-forward math is pure and runs live.
    s0 = mod.WindowState(offset=0, total_processed=0, window_size=5, n_records=20)
    s1 = mod.advance_window(s0, 5)
    if s1.offset != 5 or s1.total_processed != 5:
        return (False, "advance_window must advance the offset and add the processed count (live)")

    src = _module_source("child_continue")
    if "execute_workflow(" not in src:
        return (False, "run the heavy step as a child with workflows.execute_workflow(Child, ...)")
    if "continue_as_new(" not in src:
        return (False, "reset history with workflow.continue_as_new(state) when work remains")
    if "schedules.schedule_workflow(" not in src:
        return (False, "register the recurring run via client.workflows.schedules.schedule_workflow")
    if not isinstance(mod.build_processor_schedule(), ScheduleDefinition):
        return (False, "build_processor_schedule must return a ScheduleDefinition (live)")

    if workflows.get_workflow_definition(mod.EnrichStep).name != "enrich-step":
        return (False, "child must register as 'enrich-step'")
    if workflows.get_workflow_definition(mod.WindowedProcessor).name != "windowed-processor":
        return (False, "parent must register as 'windowed-processor'")
    return (True, "advance_window math (live); child + continue-as-new + schedule (source + SDK)")


# ---- Task 10: connector slot (structural via real SDK) --------------------------------
def t10():
    import mistralai.workflows as workflows
    mod = _fresh("connectors")

    if not _is_activity(mod.list_repo_issues):
        return (False, "list_repo_issues must be an @activity")

    src = _module_source("connectors")
    if "connector(" not in src:
        return (False, "declare a Connector slot with connector('...')")
    if "uses_connectors(" not in src:
        return (False, "list the slot on the workflow with @uses_connectors(...)")
    if "Depends(" not in src or "call_tool(" not in src:
        return (False, "inject the client with Depends(...) and call it via ToolCallClient.call_tool")

    spec = workflows.get_workflow_definition(mod.RepoIssueReportWorkflow)
    if spec.name != "repo-issue-report":
        return (False, f"workflow must register as 'repo-issue-report', got {spec.name!r}")
    return (True, "connector slot + uses_connectors + Depends + call_tool (source); registers (SDK)")


# ---- Task 11: partial encryption of a sensitive field (LIVE model + SDK field) ---------
def t11():
    from mistralai.workflows.models import EncryptedStrField
    mod = _fresh("payload")

    fields = mod.TranscriptionPayload.model_fields
    if "caller_id" not in fields:
        return (False, "add a sensitive field (e.g. caller_id) to TranscriptionPayload")

    inst = mod.TranscriptionPayload(audio_id="a1")
    if not isinstance(inst.caller_id, EncryptedStrField):
        return (False, "the sensitive field must be an EncryptedStrField (partial encryption)")
    if EncryptedStrField(data="secret").data != "secret":
        return (False, "EncryptedStrField(data=...) must carry the value to encrypt (live)")

    out = asyncio.run(mod.transcribe(mod.TranscriptionPayload(audio_id="a1")))
    if not out.caller_id.data.startswith("caller-"):
        return (False, "transcribe should set the encrypted caller_id field (live)")
    return (True, "TranscriptionPayload marks a sensitive field EncryptedStrField; round-trips (live)")


# ---- Task 12: concurrency + rate limiting (LIVE activity/logic + structural) -----------
def t12():
    import mistralai.workflows as workflows
    mod = _fresh("scale")

    if asyncio.run(mod.process_record(0, "x"))["result"] != "processed:x":
        return (False, "process_record should return a processed result (live)")

    lst = mod.choose_executor({"items": [1, 2, 3]})
    if lst["executor"] != "list" or "max_concurrent_scheduled_tasks" not in lst["kwargs"]:
        return (False, "a materialized collection uses the List executor + max_concurrent_scheduled_tasks")
    off = mod.choose_executor({"index_addressable": True, "n_items": 500})
    if off["executor"] != "offset":
        return (False, "an index-addressable dataset uses the Offset executor")

    src = _module_source("scale")
    if "asyncio.gather(" not in src:
        return (False, "use asyncio.gather for the small-batch concurrency path")
    if "RateLimit(" not in src or "key=" not in src:
        return (False, "cap the shared-quota activity with RateLimit(..., key=...)")

    spec = workflows.get_workflow_definition(mod.BatchReportWorkflow)
    if spec.name != "batch-report-workflow":
        return (False, f"workflow must register as 'batch-report-workflow', got {spec.name!r}")
    return (True, "process_record + choose_executor (live); gather + RateLimit key (source); registers")


# ---- Task 13: deployments + observability + typed errors (LIVE exception + SDK) --------
def t13():
    import mistralai.workflows as workflows
    from mistralai.workflows.exceptions import ErrorCode, WorkflowsException
    mod = _fresh("ops")

    # A typed, structured error is raised for an expected bad input and runs live.
    try:
        asyncio.run(mod.charge_account("acct-1", -5))
        return (False, "charge_account must raise WorkflowsException on a non-positive amount")
    except WorkflowsException as exc:
        if exc.code != ErrorCode.INVALID_ARGUMENTS_ERROR:
            return (False, f"raise with ErrorCode.INVALID_ARGUMENTS_ERROR, got {exc.code}")
        if not mod.is_recoverable(exc):
            return (False, "a non-terminal (non-WF_XXXX) error should read as recoverable")

    if asyncio.run(mod.charge_account("acct-1", 5))["charged"] != 5:
        return (False, "charge_account should return the charged amount on a valid input (live)")

    src = _module_source("ops")
    if "DEPLOYMENT_NAME" not in src:
        return (False, "reference DEPLOYMENT_NAME (deployment routing / name collisions)")
    if "OTel" not in src and "OpenTelemetry" not in src:
        return (False, "reference the OTel trace summary (observability)")

    spec = workflows.get_workflow_definition(mod.BillingOpsWorkflow)
    if spec.name != "billing-ops-workflow":
        return (False, f"workflow must register as 'billing-ops-workflow', got {spec.name!r}")
    return (True, "typed WorkflowsException + code (live); DEPLOYMENT_NAME + OTel noted; registers (SDK)")


print(f"== Verifying {TARGET} ==")
check("T1 define a workflow + activity", t1)
check("T2 activity timeout + retries + heartbeat", t2)
check("T3 signal + query + update", t3)
check("T4 simple durable agent", t4)
check("T5 payload offloading basics", t5)
check("T6 activity flavors + dependency injection", t6)
check("T7 workflow determinism", t7)
check("T8 streaming publish + resilient resume", t8)
check("T9 child workflow + continue-as-new + schedule", t9)
check("T10 connector slot", t10)
check("T11 partial encryption of a sensitive field", t11)
check("T12 concurrency + rate limiting", t12)
check("T13 deployments + observability + typed errors", t13)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
