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
ROOT = os.path.dirname(HERE)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "solution"
TARGET_DIR = os.path.join(ROOT, TARGET)
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


print(f"== Verifying {TARGET} ==")
check("T1 define a workflow + activity", t1)
check("T2 activity timeout + retries + heartbeat", t2)
check("T3 signal + query + update", t3)
check("T4 simple durable agent", t4)
check("T5 payload offloading basics", t5)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
