"""WFLOW-300 acceptance checks. Run via verify/check.sh <starter|solution>.

Deterministic, objective checks for the L300 tasks. Where the durable orchestrator would be
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


def _src(modname: str) -> str:
    return open(os.path.join(TARGET_DIR, "pipeline", f"{modname}.py")).read()


def _is_activity(fn) -> bool:
    return hasattr(fn, "__temporal_activity_definition")


# ---- Task 7: activity config + idempotency under retry (SDK metadata + LIVE + AST) ----
def t7():
    import mistralai.workflows as workflows
    mod = _fresh("activity_config")

    # Decorator config: timeout + retries + heartbeat, read from the real SDK activity metadata.
    params = getattr(mod.charge_customer, "__wf_activity_params__", None)
    if params is None:
        return (False, "charge_customer carries no activity params - is it still an @activity?")
    if not params.get("retry_policy_max_attempts") or params["retry_policy_max_attempts"] < 2:
        return (False, "set retry_policy_max_attempts >= 2 so a transient charge failure is retried")
    if not params.get("retry_policy_backoff_coefficient"):
        return (False, "set retry_policy_backoff_coefficient (e.g. 2.0) for exponential backoff")
    if not params.get("heartbeat_timeout_seconds"):
        return (False, "set heartbeat_timeout so a stalled long call is detected before the timeout")

    # start_to_close default is 300s, so metadata can't tell explicit from default: check source.
    src = _src("activity_config")
    if "start_to_close_timeout=" not in src:
        return (False, "set an explicit start_to_close_timeout on the activity")
    if "activity_heartbeat(" not in src:
        return (False, "a long activity must call workflows.activity_heartbeat(...) to report progress")

    # Idempotency under retry (LIVE): the platform retries with the SAME inputs, so charging
    # twice with one key must not double-bill.
    mod._LEDGER.clear()
    args = ("idem-key-fixed", "cust-1", 42.0)
    asyncio.run(mod.charge_customer(*args))
    asyncio.run(mod.charge_customer(*args))  # retry with identical inputs
    if len(mod._LEDGER) != 1 or sum(mod._LEDGER.values()) != 42.0:
        return (False, f"retry with identical inputs double-charged: ledger={mod._LEDGER} (live)")

    # Guard against a fresh key per attempt: the workflow must mint a stable key with the
    # deterministic API and pass it to the charge activity.
    run_src = inspect.getsource(mod.BillingConfigWorkflow.run)
    if "workflow.uuid4" not in run_src or "charge_customer" not in run_src:
        return (False, "workflow must mint a stable key via workflow.uuid4() and pass it to charge")
    spec = workflows.get_workflow_definition(mod.BillingConfigWorkflow)
    if spec.name != "billing-config-workflow":
        return (False, f"workflow must register as 'billing-config-workflow', got {spec.name!r}")
    return (True, "timeout+retry+heartbeat set (SDK); retried charge is a no-op via workflow.uuid4() (live)")


# ---- Task 8: signal + query + update (structural via real SDK introspection) ----------
def t8():
    import mistralai.workflows as workflows
    mod = _fresh("interactions")
    spec = workflows.get_workflow_definition(mod.ReservationWorkflow)

    if not any(s.name == "release" for s in spec.signals):
        return (False, "no 'release' signal registered - the reservation cannot be told to release")
    if not any(q.name == "get_state" for q in spec.queries):
        return (False, "no 'get_state' query registered - state cannot be read from outside")
    if not any(u.name == "add_guest" for u in spec.updates):
        return (False, "no 'add_guest' update registered - cannot add a guest and get the total back")

    add_src = inspect.getsource(mod.ReservationWorkflow.add_guest)
    if "price_guest" not in add_src:
        return (False, "the add_guest update must run the price_guest activity (updates may run activities)")
    if asyncio.run(mod.price_guest("abc")) != 3.0:
        return (False, "price_guest activity should return a deterministic price (live)")
    return (True, "release signal, get_state query, add_guest update all registered (SDK) + activity live")


# ---- Task 9: Connector slot (no OBO) - structural via SDK + source --------------------
def t9():
    import mistralai.workflows as workflows
    mod = _fresh("connectors")
    spec = workflows.get_workflow_definition(mod.RepoIssueReportWorkflow)

    if spec.name != "repo-issue-report":
        return (False, f"workflow must register as 'repo-issue-report', got {spec.name!r}")
    if spec.on_behalf_of:
        return (False, "a plain Connector slot runs as the worker; do not set on_behalf_of (that is Task 6)")
    if not _is_activity(mod.list_repo_issues):
        return (False, "list_repo_issues must be an @activity to call the connector tool")

    src = _src("connectors")
    for token in ("connector(", "uses_connectors", "Depends(", "ToolCallClient", "call_tool"):
        if token not in src:
            return (False, f"connector wiring incomplete: missing {token}")
    return (True, "connector slot + uses_connectors + Depends(ToolCallClient) wired; not OBO (SDK + source)")


# ---- Task 10: offloadable field + AES-GCM encryption (LIVE crypto + model round-trip) -
def t10():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.encoding.fields_offloader import OffloadableModel
    mod = _fresh("payload_codec")

    # Offloadable large field (structural + live model instance).
    if not issubclass(mod.DocumentPayload, OffloadableModel):
        return (False, "DocumentPayload must subclass OffloadableModel to offload the large body")
    inst = mod.DocumentPayload(doc_id="d1")
    if not hasattr(inst.body, "get_value"):
        return (False, "the body field must be an OffloadableField, not a plain str")
    run_src = inspect.getsource(mod.DocumentWorkflow.run)
    if ".get_value(" in run_src:
        return (False, "do NOT call .get_value() in the workflow body - pass the field through as-is")

    # AES-GCM on the sensitive field (LIVE crypto): round-trip, unique nonces, tamper + wrong-key.
    key = mod.generate_key_hex()
    pt = b"customer-ssn: 123-45-6789"
    if mod.decrypt_payload(key, mod.encrypt_payload(key, pt)) != pt:
        return (False, "round-trip did not recover plaintext")
    if mod.encrypt_payload(key, pt) == mod.encrypt_payload(key, pt):
        return (False, "nonce reuse: two encryptions of the same plaintext are identical")
    blob = bytearray(mod.encrypt_payload(key, pt))
    blob[-1] ^= 0x01  # tamper
    try:
        mod.decrypt_payload(key, bytes(blob))
        return (False, "tampered ciphertext decrypted without error (no integrity)")
    except Exception:  # noqa: BLE001
        pass
    try:
        mod.decrypt_payload(mod.generate_key_hex(), mod.encrypt_payload(key, pt))
        return (False, "wrong key decrypted the payload")
    except Exception:  # noqa: BLE001
        pass

    spec = workflows.get_workflow_definition(mod.DocumentWorkflow)
    if spec.name != "document-workflow":
        return (False, f"workflow must register as 'document-workflow', got {spec.name!r}")
    return (True, "offloadable body passes through; AES-GCM round-trip/nonce/tamper/wrong-key hold (live)")


# ---- Task 11: activity flavors + DI + granularity (real SDK APIs + source) -----------
def t11():
    import mistralai.workflows as workflows
    mod = _fresh("flavors")

    # The three flavor APIs must be REAL SDK symbols, not invented.
    for api in ("run_activities_locally", "run_sticky_worker_session"):
        if not hasattr(workflows, api):
            return (False, f"{api} is not a real mistralai.workflows API")

    spec = workflows.get_workflow_definition(mod.ImportWorkflow)
    if spec.name != "import-workflow":
        return (False, f"workflow must register as 'import-workflow', got {spec.name!r}")

    src = _src("flavors")
    if "with workflows.run_activities_locally()" not in src:
        return (False, "local flavor must enter `with workflows.run_activities_locally():`")
    if "async with workflows.run_sticky_worker_session()" not in src:
        return (False, "sticky flavor must enter `async with workflows.run_sticky_worker_session():`")
    if "sticky_to_worker=True" not in src:
        return (False, "a sticky activity must be marked sticky_to_worker=True")
    if "Depends(" not in src:
        return (False, "DI must inject a dependency via Depends(...)")

    # Granularity: the workflow COMPOSES several small activities, not one nested mega-activity.
    activities = [n for n, o in vars(mod).items() if _is_activity(o)]
    if len(activities) < 3:
        return (False, f"granularity: compose multiple small activities, found only {activities}")

    # DI provider runs live and yields the injected model.
    if not isinstance(mod.provide_settings(), mod.Settings):
        return (False, "Depends provider must return a Settings instance")
    return (True, "regular/local/sticky flavors + Depends DI + composed granularity (SDK + source)")


# ---- Task 12: child workflow + wait gate + continue-as-new (SDK + LIVE carry math) ----
def t12():
    import mistralai.workflows as workflows
    mod = _fresh("child_continue")

    parent = workflows.get_workflow_definition(mod.WindowedProcessor)
    child = workflows.get_workflow_definition(mod.EnrichStep)
    if parent.name != "windowed-processor":
        return (False, f"parent must register as 'windowed-processor', got {parent.name!r}")
    if child.name != "enrich-step":
        return (False, f"child must register as 'enrich-step', got {child.name!r}")
    if not any(s.name == "approve_window" for s in parent.signals):
        return (False, "parent needs an 'approve_window' signal to flip the wait gate")

    run_src = inspect.getsource(mod.WindowedProcessor.run)
    for token in ("execute_workflow(", "continue_as_new(", "wait_condition", "WorkflowError"):
        if token not in run_src:
            return (False, f"parent run missing {token} (child / continue-as-new / gate / isolation)")

    # LIVE carry-forward math: fold windows until the batch is exhausted.
    state = mod.WindowState()  # offset 0, total 0, window 5, n 20
    steps = 0
    while state.offset < state.n_records and steps < 1000:
        remaining = state.n_records - state.offset
        state = mod.advance_window(state, min(state.window_size, remaining))
        steps += 1
    if state.total_processed != 20 or state.offset != 20 or steps != 4:
        return (False, f"carry-forward wrong: total={state.total_processed} offset={state.offset} steps={steps}")
    return (True, "child + wait gate + continue-as-new wired (SDK); carry-forward folds 20 in 4 windows (live)")


# ---- Task 13: durable agent + activity-as-tool (structural via real SDK objects) ------
def t13():
    import mistralai.workflows as workflows
    import mistralai.workflows.plugins.mistralai as wm
    mod = _fresh("agents")

    if not _is_activity(mod.lookup_invoice):
        return (False, "lookup_invoice must be an @activity to be promoted to a tool")
    if not isinstance(mod.build_session(), wm.RemoteSession):
        return (False, "build_session must return a RemoteSession (keeps built-in tools)")

    agent = mod.build_billing_agent()
    if not isinstance(agent, wm.Agent):
        return (False, "build_billing_agent must return a real Agent")
    if not agent.id or agent.id != mod.AGENT_ID:
        return (False, "agent must carry a stable id")
    if mod.lookup_invoice not in (agent.tools or []):
        return (False, "the activity must be wired into the agent's tools")

    spec = workflows.get_workflow_definition(mod.BillingAgentWorkflow)
    if spec.name != "billing-agent-workflow":
        return (False, f"workflow must register as 'billing-agent-workflow', got {spec.name!r}")
    if "Runner.run" not in inspect.getsource(mod.BillingAgentWorkflow.run):
        return (False, "workflow body must drive the agent with Runner.run(...)")
    return (True, "durable agent + activity-as-tool + RemoteSession + stable id (structural via SDK)")


# ---- Task 14: coordinator->specialist handoff + MCP + built-in tool (structural SDK) --
def t14():
    import mistralai.workflows as workflows
    import mistralai.workflows.plugins.mistralai as wm
    mod = _fresh("handoffs")

    coordinator = mod.build_coordinator()
    if not isinstance(coordinator, wm.Agent):
        return (False, "build_coordinator must return a real Agent")

    # Handoff: coordinator hands to a specialist Agent.
    handoffs = coordinator.handoffs or []
    if not handoffs or not all(isinstance(a, wm.Agent) for a in handoffs):
        return (False, "coordinator must declare handoffs=[specialist Agent]")

    # MCP: an external MCP client is attached.
    mcp = coordinator.mcp_clients or []
    if not any(isinstance(c, wm.MCPStreamableHTTPConfig) for c in mcp):
        return (False, "coordinator must attach an MCP client (MCPStreamableHTTPConfig)")

    # Built-in tool: a platform tool sits in the coordinator's tools; the specialist owns an activity tool.
    from mistralai.client.models import WebSearchTool
    if not any(isinstance(t, WebSearchTool) for t in (coordinator.tools or [])):
        return (False, "coordinator must include a built-in tool (WebSearchTool)")
    specialist = handoffs[0]
    if mod.create_refund not in (specialist.tools or []):
        return (False, "specialist must expose its own activity (create_refund) as a tool")

    spec = workflows.get_workflow_definition(mod.SupportHandoffWorkflow)
    if spec.name != "support-handoff-workflow":
        return (False, f"workflow must register as 'support-handoff-workflow', got {spec.name!r}")
    if "RemoteSession" not in _src("handoffs"):
        return (False, "built-in tools require a RemoteSession")
    return (True, "handoff + MCP client + built-in tool + activity tool all wired (structural via SDK)")


# ---- Task 15: interactive chat workflow via wait_for_input (structural via SDK) -------
def t15():
    import mistralai.workflows as workflows
    from mistralai.workflows import InteractiveWorkflow
    mod = _fresh("conversational")

    if not issubclass(mod.AssistantChatWorkflow, InteractiveWorkflow):
        return (False, "an interactive workflow must subclass InteractiveWorkflow")
    if not hasattr(mod.AssistantChatWorkflow, "wait_for_input"):
        return (False, "InteractiveWorkflow must provide wait_for_input")
    if not _is_activity(mod.draft_reply):
        return (False, "the between-turns work (draft_reply) must be an @activity")

    run_src = inspect.getsource(mod.AssistantChatWorkflow.run)
    if "self.wait_for_input(" not in run_src:
        return (False, "the workflow body must await self.wait_for_input(Schema, ...)")
    if "TimeoutError" not in run_src:
        return (False, "an interactive wait must handle asyncio.TimeoutError on a bounded prompt")

    spec = workflows.get_workflow_definition(mod.AssistantChatWorkflow)
    if spec.name != "assistant-chat-workflow":
        return (False, f"workflow must register as 'assistant-chat-workflow', got {spec.name!r}")
    from pydantic import BaseModel
    if not (issubclass(mod.ChatTurn, BaseModel) and issubclass(mod.SendDecision, BaseModel)):
        return (False, "wait_for_input schemas must be Pydantic models")
    return (True, "InteractiveWorkflow + typed wait_for_input + bounded prompt (structural via SDK)")


# ---- Task 16: rate limit key + client schedule_workflow (SDK metadata + offline build) -
def t16():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.rate_limiting.rate_limit import get_rate_limit
    from mistralai.workflows.models import ScheduleDefinition
    mod = _fresh("scale")

    # Rate limit: real SDK metadata on the activity, keyed to a shared budget.
    rl = get_rate_limit(mod.fetch_partner_data)
    if rl is None:
        return (False, "fetch_partner_data must carry a RateLimit on its @activity")
    if not rl.key or rl.key != mod.RATE_LIMIT_KEY:
        return (False, "the RateLimit must set a shared key so the budget spans callers")
    if rl.max_execution < 1 or rl.time_window_in_sec < 1:
        return (False, "RateLimit needs a positive max_execution and time window")

    # Schedule: offline-built ScheduleDefinition + the canonical CLIENT call site.
    sched = mod.build_report_schedule()
    if not isinstance(sched, ScheduleDefinition):
        return (False, "build_report_schedule must return a ScheduleDefinition")
    if not sched.cron_expressions:
        return (False, "the schedule must set a cron expression")
    src = _src("scale")
    if "schedules.schedule_workflow(" not in src:
        return (False, "must schedule via the client: client.workflows.schedules.schedule_workflow(...)")
    if "workflow_identifier=" not in src:
        return (False, "schedule_workflow must target the workflow by workflow_identifier")

    spec = workflows.get_workflow_definition(mod.DailyReportWorkflow)
    if spec.name != "daily-report-workflow":
        return (False, f"scheduled workflow must register as 'daily-report-workflow', got {spec.name!r}")
    return (True, "RateLimit key on activity (SDK) + client schedule_workflow with ScheduleDefinition (offline+source)")


print(f"== Verifying {TARGET} ==")
check("T1 idempotency under retry", t1)
check("T2 wait_condition + signal + timeout", t2)
check("T3 post-restart non-determinism", t3)
check("T4 concurrency executor at scale", t4)
check("T5 resilient stream resume", t5)
check("T6 per-user Connector via on-behalf-of", t6)
check("T7 activity config + idempotency under retry", t7)
check("T8 signal + query + update", t8)
check("T9 Connector slot (no OBO)", t9)
check("T10 offloadable field + AES-GCM encryption", t10)
check("T11 activity flavors + DI + granularity", t11)
check("T12 child workflow + wait gate + continue-as-new", t12)
check("T13 durable agent + activity-as-tool", t13)
check("T14 coordinator handoff + MCP + built-in tool", t14)
check("T15 interactive chat workflow (wait_for_input)", t15)
check("T16 rate-limit key + client schedule_workflow", t16)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
