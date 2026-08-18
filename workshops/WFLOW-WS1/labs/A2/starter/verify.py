#!/usr/bin/env python3
"""WFLOW-WS1 A2 verifier - resilient_confirm.

Green means: against the injected downstream fault, the execution recovered to
COMPLETED *via retry* (it took more than one attempt). That proves durability
CONFIG carried it, not luck on a clean first try.

Two modes:

  python verify.py --selftest
      Offline. No API key, no network. Confirms the workflow module imports and
      exposes a discoverable workflow name. Use this before you have a worker
      running to prove the file is wired up.

  python verify.py
      Live. Triggers the workflow against a running worker, polls to a terminal
      status, and asserts recovery-via-retry. Requires:
        * MISTRAL_API_KEY exported
        * a worker running (make start-worker) with resilient_confirm loaded

Run this from the activity root (the folder that contains src/workflows/).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
import uuid

# --- Locate and load the workflow module by path ---------------------------
# We import by file path so this works whether or not src/workflows is a package.

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_HERE, "src", "workflows", "resilient_confirm.py")

POLL_TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 3


def _fail(message: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"\n[A2] FAIL: {message}\n")
    sys.exit(1)


def _load_module():
    if not os.path.exists(_MODULE_PATH):
        _fail(
            f"cannot find {_MODULE_PATH}. Run verify.py from the activity root, "
            "the folder that contains src/workflows/resilient_confirm.py."
        )
    spec = importlib.util.spec_from_file_location("resilient_confirm", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:  # noqa: BLE001
        _fail(
            "the workflow module failed to import: "
            f"{type(exc).__name__}: {exc}. "
            "Fix the import/syntax error before running the live check."
        )
    return module


# --- Self-test (offline) ---------------------------------------------------

_REQUIRED_SYMBOLS = ("ConfirmRequest", "ConfirmResult", "confirm_order",
                     "ResilientConfirmWorkflow")


def _selftest_source_scan() -> None:
    """Fallback when the SDK is not installed: scan the source text instead.

    This keeps `--selftest` green offline (before `uv add`), matching the
    workshop pre-flight. It confirms the workflow name is discoverable and the
    expected symbols are present without importing mistralai.workflows.
    """
    if not os.path.exists(_MODULE_PATH):
        _fail(
            f"cannot find {_MODULE_PATH}. Run verify.py from the activity root, "
            "the folder that contains src/workflows/resilient_confirm.py."
        )
    with open(_MODULE_PATH, "r", encoding="utf-8") as fh:
        source = fh.read()

    if 'WORKFLOW_NAME' not in source and 'workflow.define(name=' not in source:
        _fail(
            "the workflow name is not discoverable in resilient_confirm.py "
            "(expected WORKFLOW_NAME or @workflows.workflow.define(name=...)). "
            "The live trigger needs it."
        )
    for symbol in _REQUIRED_SYMBOLS:
        if symbol not in source:
            _fail(f"expected symbol '{symbol}' is not present in the source.")

    print("[A2] SELFTEST PASS (source scan): workflow name and expected "
          "symbols are present.")
    print("     The SDK is not importable yet, so this was a static check. "
          "Run `uv add mistralai-workflows` for the full import check.")
    print("     Next: start a worker, export MISTRAL_API_KEY, then run "
          "`python verify.py` for the live check.")


def run_selftest() -> None:
    if not os.path.exists(_MODULE_PATH):
        _fail(
            f"cannot find {_MODULE_PATH}. Run verify.py from the activity root, "
            "the folder that contains src/workflows/resilient_confirm.py."
        )

    # Prefer the rich check: actually import the module.
    spec = importlib.util.spec_from_file_location("resilient_confirm", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except ModuleNotFoundError as exc:
        # SDK not installed yet: fall back to a static source scan so the
        # pre-flight is green offline. Any OTHER import error is a real bug.
        missing = (exc.name or "")
        if missing == "mistralai" or missing.startswith("mistralai"):
            _selftest_source_scan()
            return
        _fail(
            "the workflow module failed to import: "
            f"{type(exc).__name__}: {exc}. Fix the import error before running "
            "the live check."
        )
    except Exception as exc:  # noqa: BLE001
        _fail(
            "the workflow module failed to import: "
            f"{type(exc).__name__}: {exc}. "
            "Fix the import/syntax error before running the live check."
        )

    name = getattr(module, "WORKFLOW_NAME", None)
    if not name:
        _fail(
            "WORKFLOW_NAME is not defined in resilient_confirm.py, so the "
            "workflow name is not discoverable. The live trigger needs it."
        )

    for symbol in _REQUIRED_SYMBOLS:
        if not hasattr(module, symbol):
            _fail(f"expected symbol '{symbol}' is missing from the module.")

    print("[A2] SELFTEST PASS: module imports and workflow "
          f"'{name}' is discoverable.")
    print("     Next: start a worker, export MISTRAL_API_KEY, then run "
          "`python verify.py` for the live check.")


# --- Live check ------------------------------------------------------------

def _read_recorded_attempts(module, request_id: str) -> int:
    """Attempt count as recorded by the injected fault itself.

    This is deterministic ground truth for THIS lab: the fault increments an
    on-disk counter every time the activity re-enters. attempts > 1 means the
    execution was retried.

    In production you would instead read retry evidence from the execution
    history / console. See the [VERIFY] note in poll_to_terminal().
    """
    path = module._attempt_state_path(request_id)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return int(fh.read().strip() or "0")
    except (FileNotFoundError, ValueError):
        return 0


def poll_to_terminal(client, execution_id: str):
    """Poll until the execution reaches a terminal status or we give up.

    Returns the execution object, or None if it never reached a terminal state
    within POLL_TIMEOUT_SECONDS (a hang).
    """
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    last = None
    while time.time() < deadline:
        # Confirmed accessor for status/result by id.
        last = client.workflows.executions.get_workflow_execution(
            execution_id=execution_id
        )
        status = getattr(last, "status", None)
        if status in ("COMPLETED", "FAILED", "CANCELED", "TERMINATED", "TIMED_OUT"):
            return last
        # [VERIFY] Reading the exact per-attempt retry COUNT programmatically is
        # not confirmed as a typed field on the execution object. The full event
        # history (ACTIVITY_TASK_* events, e.g. via a history / get_stream_events
        # endpoint) can be counted for retries, but that accessor is [VERIFY].
        # This verifier proves recovery-via-retry from the fault's own counter
        # instead, which needs no unconfirmed SDK field.
        time.sleep(POLL_INTERVAL_SECONDS)
    return None


def run_live() -> None:
    module = _load_module()
    workflow_name = getattr(module, "WORKFLOW_NAME")

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        _fail("MISTRAL_API_KEY is not set. Export it, then re-run.")

    # Fresh request_id so the injected fault re-arms for this run.
    request_id = f"a2-{uuid.uuid4().hex[:12]}"
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"

    # Clear any stale attempt state for this id (belt and suspenders).
    stale = module._attempt_state_path(request_id)
    try:
        os.remove(stale)
    except FileNotFoundError:
        pass

    from mistralai.client import Mistral

    client = Mistral(api_key=api_key)

    print(f"[A2] triggering '{workflow_name}' (order_id={order_id}, "
          f"request_id={request_id}) against the injected fault ...")

    try:
        execution = client.workflows.execute_workflow(
            workflow_identifier=workflow_name,
            input={"order_id": order_id, "request_id": request_id},
        )
    except Exception as exc:  # noqa: BLE001
        _fail(
            "the workflow could not be started: "
            f"{type(exc).__name__}: {exc}. "
            "If the activity has no start_to_close_timeout, the platform may "
            "reject it outright. Add a start_to_close_timeout and retry."
        )

    execution_id = getattr(execution, "execution_id", None)
    if not execution_id:
        _fail("execute_workflow returned no execution_id; cannot track the run.")

    result = poll_to_terminal(client, execution_id)

    attempts = _read_recorded_attempts(module, request_id)

    # --- Incident-report reasoning -----------------------------------------
    if result is None:
        _fail(
            f"execution {execution_id} never reached a terminal state within "
            f"{POLL_TIMEOUT_SECONDS}s. The downstream wedged on attempt "
            f"{attempts} and nothing detected it. With no start_to_close_timeout "
            "and no heartbeat_timeout, a hung attempt is never given up on, so "
            "the execution hangs instead of failing over. Add a "
            "start_to_close_timeout AND a heartbeat_timeout so the wedge is "
            "caught and retried."
        )

    status = getattr(result, "status", None)

    if status != "COMPLETED":
        _fail(
            f"execution {execution_id} reached {status} after {attempts} "
            "attempt(s). If it FAILED while still failing over, is "
            "retry_policy_max_attempts below the number of attempts the fault "
            "needs to clear (the transient failures plus the one wedge)? Raise "
            "max_attempts so the retry budget outlasts the fault."
        )

    if attempts <= 1:
        _fail(
            f"execution {execution_id} reached COMPLETED but on attempt "
            f"{attempts} - the injected fault did not fire, so the retry path "
            "was not exercised and recovery was not actually proven. Re-run "
            "(each run uses a fresh request_id, which re-arms the fault)."
        )

    print(
        f"\n[A2] PASS: execution {execution_id} recovered to COMPLETED via "
        f"retry (attempts={attempts} > 1) against the injected fault. "
        "Durability config, not luck, carried it.\n"
    )


# --- Entry point -----------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Verify WFLOW-WS1 A2.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="offline check: module imports and workflow name is discoverable",
    )
    args = parser.parse_args()

    if args.selftest:
        run_selftest()
    else:
        run_live()


if __name__ == "__main__":
    main()
