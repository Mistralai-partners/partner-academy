"""WFLOW-400 acceptance checks. Run via verify/check.sh <starter|solution>.

Deterministic, objective checks for all six tasks. Structural checks use the REAL
mistralai-workflows SDK (registration / introspection). Task 3 runs live AES-GCM crypto.
Task 4/5 exercise pure-python and SDK-object logic. Prints PASS/FAIL; exit code = # failures.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import os
import sys

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


def _activity_count(path: str) -> int:
    tree = ast.parse(open(path).read())
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                target = dec.func if isinstance(dec, ast.Call) else dec
                name = detlint._dotted(target) or ""
                if name.endswith("activity"):
                    n += 1
    return n


# ---- Task 1: determinism ------------------------------------------------------------
def t1():
    path = os.path.join(TARGET_DIR, "pipeline", "processor.py")
    violations = detlint.lint_entrypoints(path)
    return (not violations, "workflow entrypoint has no non-deterministic calls"
            if not violations else f"{len(violations)} violation(s): {violations}")


# ---- Task 2: four-constraint architecture -------------------------------------------
def t2():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.encoding.fields_offloader import OffloadableModel
    from mistralai.extra.workflows.encoding import EncryptedStrField

    proc = importlib.import_module("pipeline.processor")
    msgs = []

    if not issubclass(proc.PagePayload, OffloadableModel):
        msgs.append("PagePayload must subclass OffloadableModel (constraint 1)")
    ann = proc.PagePayload.model_fields["customer_ssn"].annotation
    if ann is not EncryptedStrField:
        msgs.append("customer_ssn must be EncryptedStrField (constraint 2)")

    spec = workflows.get_workflow_definition(proc.PiiSafeProcessor)
    if not spec.enforce_determinism:
        msgs.append("workflow must enforce determinism")

    params = list(inspect.signature(proc.PiiSafeProcessor.run).parameters)
    if not ({"page", "total_processed"} <= set(params)):
        msgs.append("run() must accept carry-forward state params page/total_processed (constraint 3)")

    src = inspect.getsource(proc.PiiSafeProcessor.run)
    if "continue_as_new" not in src or "should_continue_as_new" not in src:
        msgs.append("run() must call should_continue_as_new()+continue_as_new() (constraint 3)")

    n_act = _activity_count(os.path.join(TARGET_DIR, "pipeline", "processor.py"))
    if n_act < 3:
        msgs.append(f"needs >=3 granular activities for I/O (constraint 4); found {n_act}")

    return (not msgs, "all four constraints satisfied" if not msgs else "; ".join(msgs))


# ---- Task 3: AES-GCM encryption (LIVE) ----------------------------------------------
def t3():
    codec = importlib.import_module("pipeline.codec")
    key = codec.generate_key_hex()
    pt = b"customer-ssn: 123-45-6789"

    if codec.decrypt_payload(key, codec.encrypt_payload(key, pt)) != pt:
        return (False, "round-trip did not recover plaintext")
    if codec.encrypt_payload(key, pt) == codec.encrypt_payload(key, pt):
        return (False, "nonce reuse: two encryptions of the same plaintext are identical")

    blob = bytearray(codec.encrypt_payload(key, pt))
    blob[-1] ^= 0x01  # tamper
    try:
        codec.decrypt_payload(key, bytes(blob))
        return (False, "tampered ciphertext decrypted without error (no integrity)")
    except Exception:
        pass

    other = codec.generate_key_hex()
    try:
        codec.decrypt_payload(other, codec.encrypt_payload(key, pt))
        return (False, "wrong key decrypted the payload")
    except Exception:
        pass

    return (True, "round-trip, unique nonces, tamper-detect, wrong-key-fail all hold (live AES-GCM)")


# ---- Task 4: retry backoff budget ---------------------------------------------------
def t4():
    rb = importlib.import_module("pipeline.retry_budget")
    d5 = rb.backoff_delays(5)
    if d5 != [1.0, 2.0, 4.0, 8.0]:
        return (False, f"backoff_delays(5) should be [1,2,4,8], got {d5}")
    if rb.worst_case_backoff(5) != 15.0:
        return (False, f"worst_case_backoff(5) should be 15.0, got {rb.worst_case_backoff(5)}")
    if rb.backoff_delays(1) != []:
        return (False, "backoff_delays(1) should be []")
    return (True, "exponential backoff schedule and worst-case budget are correct")


# ---- Task 5: schedule overlap + concurrency executor --------------------------------
def t5():
    from mistralai.workflows.models import ScheduleOverlapPolicy
    ops = importlib.import_module("pipeline.ops_plan")
    msgs = []
    if ops.latest_only_sync_schedule().policy.overlap != ScheduleOverlapPolicy.SKIP:
        msgs.append("latest-only sync schedule must use overlap=SKIP")
    if ops.choose_executor({"all_items_known": True})["executor"] != "list":
        msgs.append("known collection must use the List executor")
    if ops.choose_executor({"continuation_token": True})["executor"] != "chain":
        msgs.append("continuation-token stream must use the Chain executor")
    return (not msgs, "schedule + executor selection correct" if not msgs else "; ".join(msgs))


# ---- Task 6: child workflow vs activity ---------------------------------------------
def t6():
    import mistralai.workflows as workflows
    orch = importlib.import_module("pipeline.orchestrator")
    msgs = []
    if not hasattr(orch, "EnrichRecord"):
        msgs.append("enrichment must be a child workflow class EnrichRecord (not an activity)")
    else:
        workflows.get_workflow_definition(orch.EnrichRecord)  # raises if not a workflow
    workflows.get_workflow_definition(orch.BatchOrchestrator)
    src = inspect.getsource(orch.BatchOrchestrator.run)
    if "execute_workflow" not in src:
        msgs.append("parent must call workflows.execute_workflow(EnrichRecord, ...)")
    return (not msgs, "enrich-record is a child workflow invoked by the parent"
            if not msgs else "; ".join(msgs))


print(f"== Verifying {TARGET} ==")
check("T1 determinism", t1)
check("T2 four-constraint design", t2)
check("T3 AES-GCM encryption (live)", t3)
check("T4 retry backoff budget", t4)
check("T5 schedule overlap + concurrency", t5)
check("T6 child workflow vs activity", t6)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
