"""WFLOW-300 acceptance checks. Run via verify/check.sh <starter|solution>.

Deterministic, objective checks for all six L300 tasks. Where the durable orchestrator would be
required (replay, real suspension, live OBO routing), we verify the contract the SDK CAN enforce
offline: structural validation through the REAL mistralai-workflows SDK (registration /
introspection), an AST determinism linter that mirrors the sandbox's banned-call list, and pure
logic that runs live. Each check's message says whether it ran live logic or a structural check.

Prints PASS/FAIL per check; exit code = number of failures.
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)  # detlint
import detlint  # noqa: E402

TARGET = sys.argv[1] if len(sys.argv) > 1 else "solution"
if TARGET == ".":
    TARGET_DIR = HERE
else:
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
    """Import (or re-import) a target module cleanly so per-module module-level state resets."""
    full = f"pipeline.{modname}"
    if full in sys.modules:
        del sys.modules[full]
    return importlib.import_module(full)


# ---- Task 1: idempotency under retry (LIVE logic + structural) -----------------------
def t1():
    mod = _fresh("billing")
    mod._LEDGER.clear()

    # The platform retries an activity with the SAME inputs. Build those inputs from the
    # activity's real signature, then invoke it twice to simulate a timeout-then-retry.
    params = list(inspect.signature(mod.charge_customer).parameters)
    if "idempotency_key" in params:
        args = ("idem-key-fixed", "cust-1", 42.0)
    else:
        args = ("cust-1", 42.0)

    asyncio.run(mod.charge_customer(*args))
    asyncio.run(mod.charge_customer(*args))  # retry with identical inputs

    total = sum(mod._LEDGER.values())
    if len(mod._LEDGER) != 1 or total != 42.0:
        return (False, f"retry with identical inputs double-charged: ledger={mod._LEDGER} (live)")

    # Guard against the degenerate 'dedupe on customer_id' fix: the workflow must derive a
    # stable idempotency key with the deterministic API and pass it to the charge activity.
    run_src = inspect.getsource(mod.BillingWorkflow.run)
    if "workflow.uuid4" not in run_src or "charge_customer" not in run_src:
        return (False, "workflow must mint a stable key via workflow.uuid4() and pass it to charge")
    if "idempotency_key" not in params:
        return (False, "charge activity must accept the workflow-provided idempotency_key")
    return (True, "retried charge is a no-op; key is workflow.uuid4()-derived (live + structural)")


# ---- Task 2: wait_condition + signal + timeout (structural via SDK + AST) ------------
def t2():
    import mistralai.workflows as workflows
    mod = _fresh("approval")
    spec = workflows.get_workflow_definition(mod.ApprovalWorkflow)

    if not any(s.name == "approve" for s in spec.signals):
        return (False, "no 'approve' signal registered -> external approvals are dropped")

    run_src = inspect.getsource(mod.ApprovalWorkflow.run)
    if "wait_condition" not in run_src:
        return (False, "run must suspend on workflow.wait_condition (not busy-wait)")
    if "timeout" not in run_src:
        return (False, "wait_condition must pass a timeout so it cannot hang forever")
    if "TimeoutError" not in run_src:
        return (False, "run must handle asyncio.TimeoutError to cover the expiry case")
    if "while" in run_src:
        return (False, "busy-wait loop still present in the workflow body")
    return (True, "approve signal registered; suspends with a handled timeout (structural)")


# ---- Task 3: post-restart non-determinism (AST lint + SDK registration) --------------
def t3():
    import mistralai.workflows as workflows
    mod = _fresh("determinism")
    path = os.path.join(TARGET_DIR, "pipeline", "determinism.py")
    violations = detlint.lint_entrypoints(path)
    if violations:
        return (False, f"workflow body still non-deterministic: {violations}")
    spec = workflows.get_workflow_definition(mod.ReportWorkflow)
    if not spec.enforce_determinism:
        return (False, "workflow must keep determinism enforcement on")
    return (True, "workflow body has zero non-deterministic calls; enforcement on (AST + SDK)")


# ---- Task 4: choose the right executor at scale (LIVE logic + real SDK objects) -------
def t4():
    import mistralai.workflows as workflows
    mod = _fresh("scale")
    msgs = []

    offset = mod.choose_executor({"index_addressable": True, "n_items": 500_000})
    if offset["executor"] != "offset":
        msgs.append("500k index-addressable records must use the Offset executor")
    else:
        k = offset["kwargs"]
        if k.get("n_items") != 500_000:
            msgs.append("offset plan must pass n_items")
        if "max_concurrent_executions_per_worker" not in k:
            msgs.append("offset plan must set max_concurrent_executions_per_worker")
        act = k.get("get_item_from_index_activity")
        if not hasattr(act, "__temporal_activity_definition"):
            msgs.append("offset get_item_from_index_activity must be a real @activity")

    chain = mod.choose_executor({"continuation_token": True})
    if chain["executor"] != "chain":
        msgs.append("continuation-token stream must use the Chain executor")
    elif "max_concurrent_executions_per_worker" in chain["kwargs"]:
        msgs.append("Chain executor takes no concurrency knobs")

    lst = mod.choose_executor({"items": [{"record_id": 1, "value": "a"}]})
    if lst["executor"] != "list":
        msgs.append("a materialized collection must use the List executor")
    elif "max_concurrent_executions_per_worker" in lst["kwargs"]:
        msgs.append("List plan must not carry the offset-only max_concurrent_executions_per_worker")

    # Real SDK object: the offset activity signature is validated against GetItemFromIndexParams.
    workflows.GetItemFromIndexParams(idx=0, extra_params={})
    return (not msgs, "executor selection + params correct for all three sources (live + SDK)"
            if not msgs else "; ".join(msgs))


# ---- Task 5: resilient stream resume (LIVE logic, fully offline) ---------------------
def t5():
    mod = _fresh("stream_resume")
    msgs = []

    if mod.next_start_seq(41) != 42:
        msgs.append(f"resume offset after seq 41 must be 42, got {mod.next_start_seq(41)}")

    broker = mod.EventBroker(n=6)
    result = mod.consume_stream(broker)
    delivered = result["delivered"]
    expected = [1, 2, 3, 4, 5, 6]
    if delivered != expected:
        # ordered, unique, no gaps across the forced reconnect
        if sorted(set(delivered)) == expected and len(delivered) != len(set(delivered)):
            msgs.append(f"reconnect re-delivered an event (duplicate): {delivered}")
        else:
            msgs.append(f"stream not delivered exactly once in order: {delivered}")

    schedule = [mod.reconnect_backoff(i) for i in range(5)]
    if not all(b < a for b, a in zip(schedule, schedule[1:]) if a < 8.0):
        msgs.append(f"reconnect backoff must grow until the cap, got {schedule}")
    if schedule[-1] > 8.0:
        msgs.append(f"reconnect backoff must be capped, got {schedule}")

    return (not msgs, "resume offset, gap/dup-free delivery, capped backoff all hold (live)"
            if not msgs else "; ".join(msgs))


# ---- Task 6: per-user Connector access via on-behalf-of (structural via SDK) ---------
def t6():
    import mistralai.workflows as workflows
    mod = _fresh("obo")
    spec = workflows.get_workflow_definition(mod.UserPrReportWorkflow)
    if not spec.on_behalf_of:
        return (False, "workflow runs as the worker; set on_behalf_of=True for per-user identity")
    if spec.schedules:
        return (False, "on_behalf_of cannot be combined with schedules (no triggering user)")
    return (True, "workflow runs on-behalf-of the triggering user; no schedule conflict (SDK)")


print(f"== Verifying {TARGET} ==")
check("T1 idempotency under retry", t1)
check("T2 wait_condition + signal + timeout", t2)
check("T3 post-restart non-determinism", t3)
check("T4 concurrency executor at scale", t4)
check("T5 resilient stream resume", t5)
check("T6 per-user Connector via on-behalf-of", t6)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
