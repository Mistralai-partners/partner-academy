"""WFLOW-TSE1 acceptance checks. Run via verify/check.sh <starter|solution>.

Deterministic, objective checks for the four TSE tasks. Two kinds of check, labelled honestly in
every message:

- STRUCTURAL via the REAL mistralai-workflows SDK. T1 and T2 build the demo workflow and we
  introspect it through the actual SDK (registration, get_workflow_definition, activity markers).
  Actually *executing* a workflow (replay after a restart, a live query against a running execution)
  needs the hosted orchestrator plus a running worker, which is not an offline, deterministic
  self-check. So we verify what the SDK CAN confirm offline: that the definition the seller would
  deploy is well-formed and tells the durability story (activity boundary, deterministic id source,
  query and signal registered, determinism enforced). Nothing is mocked; nothing fakes a pass.

- LIVE logic (fully offline). T3 and T4 run the learner's scoping map and feasibility decisions as
  real Python and check them against a fixed rubric.

Prints PASS/FAIL per check; exit code = number of failures.
"""
from __future__ import annotations

import importlib
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "solution"
TARGET_DIR = os.path.join(ROOT, TARGET)
sys.path.insert(0, TARGET_DIR)  # so `import demo.*` resolves to the target tree

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


def _load(modname: str):
    full = f"demo.{modname}"
    if full in sys.modules:
        del sys.modules[full]
    return importlib.import_module(full)


# Import the demo workflow ONCE so the @workflow.define decorator registers "invoice-demo" a single
# time; T1 and T2 both introspect this same module.
_invoice = _load("invoice_workflow")


# ---- T1: build the durable demo (STRUCTURAL via real SDK) -----------------------------
def t1():
    mod = _invoice
    # A real @activity must exist for the side effect (activities carry the SDK's marker attr).
    activities = [
        n for n, obj in vars(mod).items()
        if callable(obj) and hasattr(obj, "__temporal_activity_definition")
    ]
    if not activities:
        return (False, "no @activity defined: the PDF fetch is still inline, so it is not the "
                       "retry boundary and the durability story does not hold")

    run_src = inspect.getsource(mod.InvoiceWorkflow.run)
    if not any(a in run_src for a in activities) or "await" not in run_src:
        return (False, "the workflow body must await the fetch activity, not run the fetch inline")
    if "uuid.uuid4(" in run_src:
        return (False, "raw uuid.uuid4() in the workflow body breaks replay; use workflow.uuid4()")
    if "workflow.uuid4(" not in run_src:
        return (False, "the id must come from the deterministic workflow.uuid4()")

    import mistralai.workflows as workflows
    spec = workflows.get_workflow_definition(mod.InvoiceWorkflow)
    if not spec.enforce_determinism:
        return (False, "determinism enforcement must stay on for a replay-safe demo")
    return (True, f"activity boundary + deterministic id + enforcement on ({activities[0]}) "
                  "(structural via SDK)")


# ---- T2: make the demo interactive (STRUCTURAL via real SDK) --------------------------
def t2():
    import mistralai.workflows as workflows
    spec = workflows.get_workflow_definition(_invoice.InvoiceWorkflow)
    if not any(q.name == "get_status" for q in spec.queries):
        return (False, "no get_status query: the customer cannot watch progress live in the demo")
    if not any(s.name == "approve" for s in spec.signals):
        return (False, "no approve signal: the human-in-the-loop approval story is missing")
    return (True, "get_status query + approve signal registered (structural via SDK)")


# ---- T3: scope the fit (LIVE logic, offline) ------------------------------------------
def t3():
    mod = _load("scoping")
    expected = {
        "call_external_http_api": "activity",
        "watch_progress_live": "query",
        "human_approval_midrun": "signal",
        "handle_files_over_2mb": "payload_offloading",
        "reuse_loaded_model_across_steps": "sticky_worker_session",
        "platform_never_sees_cleartext": "encryption",
    }
    got = dict(getattr(mod, "SCOPING", {}))
    wrong = {k: got.get(k, "<missing>") for k, v in expected.items() if got.get(k) != v}
    if wrong:
        return (False, f"wrong capability for: {wrong} (each need maps to exactly one primitive)")
    return (True, "all six customer needs mapped to the right capability (live)")


# ---- T4: feasibility / honest architecture answer (LIVE logic, offline) ---------------
def t4():
    mod = _load("feasibility")
    expected = {
        "per_user_connectors": {
            "verdict": "GO_WITH_CAVEAT", "constraint": "obo_requires_hardened_deployment"},
        "scheduled_per_user_report": {
            "verdict": "NO_FIT", "constraint": "obo_incompatible_with_schedules"},
        "durable_slow_partner_call": {
            "verdict": "GO", "constraint": "side_effects_go_in_activities"},
    }
    wrong = []
    for sid, want in expected.items():
        got = mod.assess(sid)
        if got != want:
            wrong.append(f"{sid}: got {got}, expected {want}")
    if wrong:
        return (False, "; ".join(wrong))
    return (True, "OBO/hardening/schedule constraints called correctly, no over-promise (live)")


print(f"== Verifying {TARGET} ==")
check("T1 build the durable demo", t1)
check("T2 make the demo interactive (query + signal)", t2)
check("T3 scope the fit", t3)
check("T4 feasibility (honest architecture answer)", t4)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
