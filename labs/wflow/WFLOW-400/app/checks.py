"""WFLOW-400 acceptance checks — one task per content lesson (T1-T16).

Deterministic, objective checks for the sixteen expert lessons. Structural checks use the REAL
mistralai-workflows SDK (registration / introspection). Live crypto (AES-GCM, key rotation) and all
pure logic run for real. Platform-only behaviour (agent loop, live OAuth/OBO, live SSE consume, live
Vibe render, live schedule create/pause/resume, live reset/routing, live traces) is verified
STRUCTURALLY via real SDK objects plus an offline pure-logic sibling, and each check's message says
which mode it used. No check fakes a pass.

Task -> lesson map (blueprint 06-lab-build-blueprint.md):
  T1  L1.1 mental_model     T5  L3.1 interactions   T9   L5.1 streaming      T13 L6.2 processor+codec
  T2  L1.2 determinism      T6  L3.2 orchestrator   T10  L5.2 consume        T14 L7.1 scheduling
  T3  L2.1 activity_config  T7  L4.1 agent          T11  L5.3 conversational T15 L7.2 deployment
  T4  L2.2 flavors          T8  L4.2 connectors     T12  L6.1 concurrency    T16 L7.3 observability

Prints PASS/FAIL per check; exit code = number of failures.
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


def _mod(modname: str):
    return importlib.import_module(f"pipeline.{modname}")


def _src(modname: str) -> str:
    return open(os.path.join(TARGET_DIR, "pipeline", f"{modname}.py")).read()


def _is_activity(fn) -> bool:
    return hasattr(fn, "__temporal_activity_definition")


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


# ---- T1 (L1.1): execution mental model + history-cap math ----------------------------
def t1():
    import mistralai.workflows as workflows
    mm = _mod("mental_model")
    msgs = []
    if mm.events_per_iteration(3) != 12:
        msgs.append(f"events_per_iteration(3) should be 12, got {mm.events_per_iteration(3)}")
    if mm.iterations_until_cap(12) != 51_200 // 12:
        msgs.append("iterations_until_cap must floor cap/per-iteration")
    cadence = mm.safe_continue_as_new_cadence(12)
    if cadence >= mm.iterations_until_cap(12) or cadence != int(51_200 * 0.8 // 12):
        msgs.append("safe cadence must reset below the hard cap (default 80% margin)")
    spec = workflows.get_workflow_definition(mm.HeartbeatEcho)
    if spec.name != "heartbeat-echo":
        msgs.append(f"HeartbeatEcho must register as 'heartbeat-echo', got {spec.name!r}")
    return (not msgs, "history-cap math exact + minimal workflow registers (offline + SDK)"
            if not msgs else "; ".join(msgs))


# ---- T2 (L1.2): determinism enforcement + linter on good vs anti-pattern -------------
def t2():
    import mistralai.workflows as workflows
    det = _mod("determinism")
    good = detlint.lint_entrypoints(os.path.join(TARGET_DIR, "pipeline", "determinism.py"))
    if good:
        return (False, f"good workflow body still has non-deterministic calls: {good}")
    bad = detlint.lint_entrypoints(os.path.join(TARGET_DIR, "pipeline", "determinism_antipattern.py"))
    if not bad:
        return (False, "the bundled anti-pattern should be flagged by the linter but was not")
    spec = workflows.get_workflow_definition(det.StampWorkflow)
    if not spec.enforce_determinism:
        return (False, "StampWorkflow must keep determinism enforcement on")
    if det.preferred_fix("datetime.now") != "deterministic_workflow_api":
        return (False, "a time/uuid/random issue should prefer the deterministic workflow API")
    if det.preferred_fix("open") != "move_to_activity":
        return (False, "an I/O issue should prefer moving the side effect to an activity")
    return (True, f"good body lints clean, anti-pattern flags {len(bad)}; fixes ranked (AST + SDK)")


# ---- T3 (L2.1): activity config + retry budget --------------------------------------
def t3():
    import mistralai.workflows as workflows
    ac = _mod("activity_config")
    rb = _mod("retry_budget")
    msgs = []
    if not _is_activity(ac.fetch_quote):
        msgs.append("fetch_quote must be an @activity")
    src = _src("activity_config")
    for token in ("start_to_close_timeout=", "retry_policy_max_attempts",
                  "retry_policy_backoff_coefficient", "heartbeat_timeout", "name=",
                  "activity_heartbeat("):
        if token not in src:
            msgs.append(f"activity config incomplete: missing {token}")
    spec = workflows.get_workflow_definition(ac.QuoteConfigWorkflow)
    if spec.name != "quote-config-workflow":
        msgs.append(f"workflow must register as 'quote-config-workflow', got {spec.name!r}")
    if rb.backoff_delays(5) != [1.0, 2.0, 4.0, 8.0] or rb.worst_case_backoff(5) != 15.0:
        msgs.append("retry budget math wrong (backoff_delays(5)=[1,2,4,8], worst_case=15.0)")
    return (not msgs, "timeout+retry+heartbeat+name set (SDK/source); retry budget correct (live)"
            if not msgs else "; ".join(msgs))


# ---- T4 (L2.2): activity flavors + DI + granularity ---------------------------------
def t4():
    import mistralai.workflows as workflows
    fl = _mod("flavors")
    msgs = []
    for api in ("run_activities_locally", "run_sticky_worker_session"):
        if not hasattr(workflows, api):
            msgs.append(f"{api} is not a real mistralai.workflows API")
    if fl.choose_flavor({"side_effect": True}) != "regular":
        msgs.append("a real side effect must choose the regular flavor")
    if fl.choose_flavor({"pure_cpu": True, "tiny": True}) != "local":
        msgs.append("a tiny pure-CPU transform must choose the local flavor")
    if fl.choose_flavor({"reuses_warm_state": True}) != "sticky":
        msgs.append("a warm-state call must choose the sticky flavor")
    src = _src("flavors")
    if "with workflows.run_activities_locally()" not in src:
        msgs.append("local flavor must enter `with workflows.run_activities_locally():`")
    if "async with workflows.run_sticky_worker_session()" not in src:
        msgs.append("sticky flavor must enter `async with workflows.run_sticky_worker_session():`")
    if "sticky_to_worker=True" not in src or "Depends(" not in src:
        msgs.append("need a sticky_to_worker=True activity and a Depends(...) injection")
    spec = workflows.get_workflow_definition(fl.ImportFlavorsWorkflow)
    if spec.name != "import-flavors-workflow":
        msgs.append(f"workflow must register as 'import-flavors-workflow', got {spec.name!r}")
    return (not msgs, "regular/local/sticky selection + DI + three contexts (offline + SDK)"
            if not msgs else "; ".join(msgs))


# ---- T5 (L3.1): signal + query + update + wait_condition -----------------------------
def t5():
    import mistralai.workflows as workflows
    it = _mod("interactions")
    spec = workflows.get_workflow_definition(it.OrderInteractionsWorkflow)
    msgs = []
    if not any(s.name == "cancel_order" for s in spec.signals):
        msgs.append("no 'cancel_order' signal registered")
    if not any(q.name == "get_status" for q in spec.queries):
        msgs.append("no 'get_status' query registered")
    if not any(u.name == "add_item" for u in spec.updates):
        msgs.append("no 'add_item' update registered")
    if "price_item" not in inspect.getsource(it.OrderInteractionsWorkflow.add_item):
        msgs.append("the add_item update must run the price_item activity")
    if it.validate_add_item({"sku": "abc"})[0] is not True:
        msgs.append("validate_add_item should accept a valid payload")
    if it.validate_add_item({"sku": ""})[0] is not False:
        msgs.append("validate_add_item should reject an empty sku")
    return (not msgs, "signal+query+update registered (SDK) + payload validation (offline)"
            if not msgs else "; ".join(msgs))


# ---- T6 (L3.2): child workflow vs activity + error classification --------------------
def t6():
    import mistralai.workflows as workflows
    from mistralai.workflows.exceptions import ErrorCode, WorkflowsException
    orch = _mod("orchestrator")
    msgs = []
    workflows.get_workflow_definition(orch.EnrichRecord)   # raises if not a workflow
    workflows.get_workflow_definition(orch.BatchOrchestrator)
    if "execute_workflow" not in inspect.getsource(orch.BatchOrchestrator.run):
        msgs.append("parent must call workflows.execute_workflow(EnrichRecord, ...)")
    verdict = orch.classify_error(
        WorkflowsException(message="bad", code=ErrorCode.INVALID_ARGUMENTS_ERROR)
    )
    if verdict["terminal"] is not False or verdict["action"] != "retry":
        msgs.append(f"a non-terminal error should classify as retryable, got {verdict}")
    return (not msgs, "child workflow via execute_workflow (SDK) + error triage (live)"
            if not msgs else "; ".join(msgs))


# ---- T7 (L4.1): durable agent (create-fresh) + safe per-worker MCP credentials ------
def t7():
    import mistralai.workflows as workflows
    import mistralai.workflows.plugins.mistralai as wm
    ag = _mod("agent")
    src = _src("agent")
    msgs = []
    if not _is_activity(ag.lookup_doc):
        msgs.append("lookup_doc must be an @activity to be a tool")
    if not isinstance(ag.build_session(), wm.RemoteSession):
        msgs.append("build_session must return a RemoteSession")
    # Create-fresh: the workflow's agent must carry NO hardcoded id. The platform assigns the id on
    # create; a made-up string id sends RemoteSession down its update_agent branch, which 404s.
    agent = ag.build_docs_agent()
    if not isinstance(agent, wm.Agent):
        msgs.append("build_docs_agent must return an Agent")
    elif agent.id is not None:
        msgs.append("build_docs_agent must be create-fresh (no hardcoded id; the platform assigns it)")
    if "build_docs_agent()" not in src:
        msgs.append("the workflow must build its agent create-fresh via build_docs_agent()")
    if ag.lookup_doc not in (agent.tools or []):
        msgs.append("the activity must be wired into the agent's tools")
    # A real, resolvable MCP server is wired into the workflow's agent (not the placeholder).
    wired = agent.mcp_clients or []
    if not any(isinstance(c, wm.MCPStreamableHTTPConfig) for c in wired):
        msgs.append("the agent must attach a real MCPStreamableHTTPConfig")
    if not any(c.url.startswith("https://") and "example.com" not in c.url for c in wired):
        msgs.append("the wired MCP url must be a real https server, not a placeholder like example.com")
    if "example.com" in src:
        msgs.append("no placeholder MCP url (example.com) may remain in the module")
    # Per-worker credential EXAMPLE: real config objects, env-var names only, distinct per identity.
    for cfg in (ag.MCP_WORKER_A, ag.MCP_WORKER_B):
        if not isinstance(cfg, wm.MCPStreamableHTTPConfig):
            msgs.append("MCP worker configs must be real MCPStreamableHTTPConfig objects")
        if not cfg.auth_token_env:
            msgs.append("each worker config must reference its credential via an env-var name (auth_token_env)")
    if ag.MCP_WORKER_A.auth_token_env == ag.MCP_WORKER_B.auth_token_env:
        msgs.append("the two workers must read DIFFERENT key env vars (per-worker identity)")
    # Credentials are env-var NAMES, not secret values: every reference is an uppercase env-var
    # identifier the worker resolves at runtime, so no secret is serialized into history or source.
    mapped_values = [ag.MCP_WORKER_A.auth_token_env, ag.MCP_WORKER_B.auth_token_env]
    mapped_values += list((ag.MCP_WORKER_A.header_mapping or {}).values())
    mapped_values += list((ag.MCP_WORKER_B.header_mapping or {}).values())
    if not all(v.replace("_", "").isalnum() and v.upper() == v for v in mapped_values):
        msgs.append("MCP credentials must be referenced by uppercase env-var names, never literal secrets")
    spec = workflows.get_workflow_definition(ag.DocsAgentWorkflow)
    if spec.name != "docs-agent-workflow" or "Runner.run" not in inspect.getsource(ag.DocsAgentWorkflow.run):
        msgs.append("workflow must register as 'docs-agent-workflow' and drive Runner.run(...)")
    return (not msgs, "create-fresh agent + activity-tool + real MCP + per-worker env-mapping, no literal secret (SDK)"
            if not msgs else "; ".join(msgs))


# ---- T8 (L4.2): connector slot + OAuth on-behalf-of ---------------------------------
def t8():
    import mistralai.workflows as workflows
    conn = _mod("connectors")
    msgs = []
    spec = workflows.get_workflow_definition(conn.UserPrReportWorkflow)
    if spec.name != "user-pr-report":
        msgs.append(f"workflow must register as 'user-pr-report', got {spec.name!r}")
    if not spec.on_behalf_of:
        msgs.append("OBO workflow must set on_behalf_of=True for per-user identity")
    if not _is_activity(conn.list_user_prs):
        msgs.append("list_user_prs must be an @activity to call the connector tool")
    src = _src("connectors")
    for token in ("connector(", "uses_connectors", "Depends(", "ToolCallClient", "call_tool",
                  "execute_with_connector_auth_async", "on_auth_required", ".auth_url",
                  "ConnectorSlot"):
        if token not in src:
            msgs.append(f"OBO/connector wiring incomplete: missing {token}")
    if conn.resolve_identity(True) != "triggering_user" or conn.resolve_identity(False) != "worker_service_account":
        msgs.append("identity resolution rule wrong (OBO=triggering_user, plain=worker)")
    return (not msgs, "slot + uses_connectors + Depends + OBO/OAuth shapes (SDK/source) + identity (offline)"
            if not msgs else "; ".join(msgs))


# ---- T9 (L5.1): publish a streaming event (broker_sequence) --------------------------
def t9():
    import mistralai.workflows as workflows
    st = _mod("streaming")
    msgs = []
    if not _is_activity(st.stream_tokens):
        msgs.append("stream_tokens must be an @activity")
    src = _src("streaming")
    if "workflows.task(" not in src or "update_state(" not in src:
        msgs.append("publish side must use workflows.task(...) + update_state(...)")
    spec = workflows.get_workflow_definition(st.StreamingPublishWorkflow)
    if spec.name != "streaming-publish-workflow":
        msgs.append(f"workflow must register as 'streaming-publish-workflow', got {spec.name!r}")
    if st.next_start_seq(41) != 42:
        msgs.append("next_start_seq(41) must be 42 (advance by one)")
    return (not msgs, "publish-side task()/update_state + registers (SDK) + resume arithmetic (live)"
            if not msgs else "; ".join(msgs))


# ---- T10 (L5.2): consume an event stream resiliently --------------------------------
def t10():
    cs = _mod("consume")
    msgs = []
    if cs.next_start_seq(41) != 42:
        msgs.append("next_start_seq(41) must be 42")
    if not cs.is_terminal_status("WORKFLOW_EXECUTION_COMPLETED"):
        msgs.append("COMPLETED must be detected as terminal")
    if cs.is_terminal_status("ACTIVITY_TASK_STARTED"):
        msgs.append("a non-terminal event must not be treated as terminal")
    schedule = [cs.reconnect_backoff(i) for i in range(6)]
    if not all(b <= a for b, a in zip(schedule, schedule[1:])) or schedule[-1] > 30.0:
        msgs.append(f"reconnect backoff must grow monotonically and cap at 30, got {schedule}")
    src = _src("consume")
    for token in ("get_stream_events(", "broker_sequence + 1", "start_seq="):
        if token not in src:
            msgs.append(f"consumer shape incomplete: missing {token}")
    return (not msgs, "resume-seq + terminal-detect + capped backoff (live); get_stream_events shape (source)"
            if not msgs else "; ".join(msgs))


# ---- T11 (L5.3): Vibe-compatible conversational workflow ----------------------------
def t11():
    import mistralai.workflows as workflows
    from mistralai.workflows import InteractiveWorkflow
    cv = _mod("conversational")
    msgs = []
    if not issubclass(cv.AssistantVibeWorkflow, InteractiveWorkflow):
        msgs.append("a conversational workflow must subclass InteractiveWorkflow")
    if not _is_activity(cv.draft_reply):
        msgs.append("between-turns work (draft_reply) must be an @activity")
    src = _src("conversational")
    for token in ("send_assistant_message(", "self.wait_for_input(", "ChatInput(",
                  "ChatAssistantWorkflowOutput(", "TextOutput(", "timeout", "TimeoutError"):
        if token not in src:
            msgs.append(f"Vibe contract incomplete: missing {token}")
    ret = inspect.signature(cv.AssistantVibeWorkflow.run).return_annotation
    if "ChatAssistantWorkflowOutput" not in str(ret):
        msgs.append("run must be annotated to return ChatAssistantWorkflowOutput (Vibe contract)")
    spec = workflows.get_workflow_definition(cv.AssistantVibeWorkflow)
    if spec.name != "assistant-vibe-workflow" or getattr(spec, "display_name", None) != "Assistant":
        msgs.append("workflow must register as 'assistant-vibe-workflow' with a Vibe display name")
    return (not msgs, "InteractiveWorkflow + send/wait/ChatInput + ChatAssistantWorkflowOutput (SDK)"
            if not msgs else "; ".join(msgs))


# ---- T12 (L6.1): concurrency executors (List/Chain/Offset) --------------------------
def t12():
    import mistralai.workflows as workflows
    cc = _mod("concurrency")
    ops = _mod("ops_plan")
    msgs = []
    if ops.choose_executor({"all_items_known": True})["executor"] != "list":
        msgs.append("known collection must select the List executor")
    if ops.choose_executor({"continuation_token": True})["executor"] != "chain":
        msgs.append("continuation-token stream must select the Chain executor")
    if ops.choose_executor({"n_items": 500})["executor"] != "offset":
        msgs.append("index-addressable pages must select the Offset executor")
    for cls, name in ((cc.ListConcurrencyWorkflow, "list-concurrency-workflow"),
                      (cc.OffsetConcurrencyWorkflow, "offset-concurrency-workflow")):
        spec = workflows.get_workflow_definition(cls)
        if spec.name != name:
            msgs.append(f"workflow must register as {name!r}, got {spec.name!r}")
    src = _src("concurrency")
    if "execute_activities_in_parallel(" not in src or "get_item_from_index_activity=" not in src:
        msgs.append("must call execute_activities_in_parallel with List and Offset shapes")
    workflows.GetItemFromIndexParams(idx=0, extra_params={})  # real SDK object
    return (not msgs, "executor selection (offline) + List/Offset workflows register (SDK)"
            if not msgs else "; ".join(msgs))


# ---- T13 (L6.2): payload offload + AES-GCM + key rotation ----------------------------
def t13():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.encoding.fields_offloader import OffloadableModel
    from mistralai.extra.workflows.encoding import EncryptedStrField
    proc = _mod("processor")
    codec = _mod("codec")
    msgs = []

    # Four-constraint design (offload + encrypt-at-rest + continue-as-new + granular activities).
    if not issubclass(proc.PagePayload, OffloadableModel):
        msgs.append("PagePayload must subclass OffloadableModel (offload)")
    if proc.PagePayload.model_fields["customer_ssn"].annotation is not EncryptedStrField:
        msgs.append("customer_ssn must be EncryptedStrField (encrypted at rest)")
    if not workflows.get_workflow_definition(proc.PiiSafeProcessor).enforce_determinism:
        msgs.append("processor must enforce determinism")
    run_src = inspect.getsource(proc.PiiSafeProcessor.run)
    if "continue_as_new" not in run_src or "should_continue_as_new" not in run_src:
        msgs.append("run() must reset history via should_continue_as_new()+continue_as_new()")
    if _activity_count(os.path.join(TARGET_DIR, "pipeline", "processor.py")) < 3:
        msgs.append("needs >=3 granular activities for I/O")

    # Live AES-GCM: round-trip, unique nonces, tamper-detect, wrong-key-fail.
    key = codec.generate_key_hex()
    pt = b"customer-ssn: 123-45-6789"
    if codec.decrypt_payload(key, codec.encrypt_payload(key, pt)) != pt:
        msgs.append("AES-GCM round-trip did not recover plaintext")
    if codec.encrypt_payload(key, pt) == codec.encrypt_payload(key, pt):
        msgs.append("nonce reuse: two encryptions are identical")
    blob = bytearray(codec.encrypt_payload(key, pt)); blob[-1] ^= 0x01
    try:
        codec.decrypt_payload(key, bytes(blob)); msgs.append("tampered ciphertext decrypted (no integrity)")
    except Exception:  # noqa: BLE001
        pass

    # Key rotation: decrypt-with-old, re-encrypt-with-new; old key can no longer read it.
    old, new = codec.generate_key_hex(), codec.generate_key_hex()
    original = codec.encrypt_payload(old, pt)
    rotated = codec.rotate_key(old, new, original)
    if codec.decrypt_payload(new, rotated) != pt:
        msgs.append("rotate_key must keep the plaintext readable under the new key")
    try:
        codec.decrypt_payload(old, rotated); msgs.append("old key must not read the rotated blob")
    except Exception:  # noqa: BLE001
        pass

    return (not msgs, "four-constraint design (SDK) + AES-GCM + key rotation round-trip (live)"
            if not msgs else "; ".join(msgs))


# ---- T14 (L7.1): scheduling — calendars, interval+jitter, overlap -------------------
def t14():
    from mistralai.workflows.models import (
        ScheduleDefinition, ScheduleOverlapPolicy,
    )
    sc = _mod("scheduling")
    ops = _mod("ops_plan")
    msgs = []
    cal = sc.weekday_business_hours_schedule()
    if not isinstance(cal, ScheduleDefinition) or not cal.calendars:
        msgs.append("weekday schedule must be a ScheduleDefinition with calendars")
    jit = sc.hourly_jittered_schedule()
    if not jit.intervals or not jit.jitter:
        msgs.append("jittered schedule must set intervals + jitter")
    if not sc.cron_nightly_schedule().cron_expressions:
        msgs.append("cron schedule must set cron_expressions")
    if sc.minute_of_day(9, 0) != 540 or sc.minute_of_day(8, 30) != 510:
        msgs.append("fire-time math (minute_of_day) wrong")
    if ops.latest_only_sync_schedule().policy.overlap != ScheduleOverlapPolicy.SKIP:
        msgs.append("latest-only sync schedule must use overlap=SKIP")
    src = _src("scheduling")
    if "schedule_workflow(" not in src or "deployment_name=" not in src:
        msgs.append("must register via client schedule_workflow(..., deployment_name=...)")
    return (not msgs, "calendar/interval+jitter/cron build via SDK + fire-time/overlap (offline)"
            if not msgs else "; ".join(msgs))


# ---- T15 (L7.2): deployment routing, poller budget, reset ---------------------------
def t15():
    import mistralai.workflows as workflows
    from mistralai.workflows.core.rate_limiting.rate_limit import get_rate_limit
    dep = _mod("deployment")
    msgs = []
    regs = {"prod": ["w"], "staging": ["w"]}
    if dep.resolve_routing("w", regs)["status"] != "ambiguous":
        msgs.append("two deployments registering the same name must be flagged ambiguous")
    if dep.resolve_routing("w", {"prod": ["w"]})["deployment"] != "prod":
        msgs.append("a uniquely-registered name must route to its deployment")
    if dep.resolve_routing("x", {"prod": ["w"]})["status"] != "unrouted":
        msgs.append("an unregistered name must be unrouted")
    if dep.poller_budget(10, 4) != 2 or dep.poller_budget(5, 5) != 1:
        msgs.append("poller_budget must floor total capacity across workers")
    events = [{"event_type": "WORKFLOW_TASK_COMPLETED", "event_id": 7},
              {"event_type": "ACTIVITY_TASK_STARTED", "event_id": 8}]
    if dep.valid_reset_points(events) != [7]:
        msgs.append("valid_reset_points must keep only WORKFLOW_TASK_COMPLETED ids")
    rl = get_rate_limit(dep.fetch_partner_data)
    if rl is None or rl.key != dep.RATE_LIMIT_KEY:
        msgs.append("fetch_partner_data must carry a keyed RateLimit")
    spec = workflows.get_workflow_definition(dep.DeploymentOpsWorkflow)
    if spec.name != "deployment-ops-workflow":
        msgs.append(f"workflow must register as 'deployment-ops-workflow', got {spec.name!r}")
    src = _src("deployment")
    for token in ("reset_workflow(", "WORKFLOW_TASK_COMPLETED", "get_workflow_execution_trace_events("):
        if token not in src:
            msgs.append(f"reset shape incomplete: missing {token}")
    return (not msgs, "routing + poller budget + reset points (offline) + keyed RateLimit (SDK)"
            if not msgs else "; ".join(msgs))


# ---- T16 (L7.3): observability traces + error-code classification -------------------
def t16():
    from mistralai.workflows.exceptions import ErrorCode, WorkflowsException
    obs = _mod("observability")
    msgs = []
    invalid = obs.classify_error_code(
        WorkflowsException(message="bad input", code=ErrorCode.INVALID_ARGUMENTS_ERROR)
    )
    if invalid["action"] != "return_to_caller":
        msgs.append(f"an input error should return to the caller, got {invalid}")
    # A non-terminal, non-input code should be left to the retry policy.
    transient = None
    for name in dir(ErrorCode):
        if not name.isupper():
            continue
        code = getattr(ErrorCode, name)
        exc = WorkflowsException(message="x", code=code)
        if not exc.is_terminal() and code not in obs._INPUT_ERROR_CODES:
            transient = obs.classify_error_code(exc)
            break
    if transient and transient["action"] != "let_retry_policy_recover":
        msgs.append(f"a transient error should defer to the retry policy, got {transient}")
    src = _src("observability")
    for token in ("get_workflow_execution_trace_otel(", "get_workflow_execution_trace_summary(",
                  "get_workflow_execution_trace_events("):
        if token not in src:
            msgs.append(f"observability shape incomplete: missing {token}")
    return (not msgs, "error-code classification (live) + three trace fetches (source boundary)"
            if not msgs else "; ".join(msgs))


print(f"== Verifying {TARGET} ==")
check("T1  L1.1 mental model + history cap", t1)
check("T2  L1.2 determinism enforcement", t2)
check("T3  L2.1 activity configuration", t3)
check("T4  L2.2 activity flavors", t4)
check("T5  L3.1 signals/queries/updates", t5)
check("T6  L3.2 child workflow + errors", t6)
check("T7  L4.1 durable agent + MCP creds", t7)
check("T8  L4.2 connectors + OBO/OAuth", t8)
check("T9  L5.1 publishing stream events", t9)
check("T10 L5.2 consuming stream events", t10)
check("T11 L5.3 conversational to Vibe", t11)
check("T12 L6.1 concurrency executors", t12)
check("T13 L6.2 offload + encrypt + rotate", t13)
check("T14 L7.1 workflow scheduling", t14)
check("T15 L7.2 deployment management", t15)
check("T16 L7.3 observability + error codes", t16)
print(f"== {TARGET}: {_pass} passed, {_fail} failed ==")
sys.exit(_fail)
