#!/usr/bin/env python3
"""A1 verification harness: Build and Run Your First Durable Workflow.

This harness runs against the workflow in `app/`. Against an unfinished workflow
(confirm_order returns None) the live check fails with a clear incident report;
against the finished workflow it passes.

Two modes:

  python verify.py --selftest
      Offline pre-flight. Loads the workflow file and confirms the workflow name
      is discoverable. No worker, no API call. Green means the files are wired
      correctly and you are ready to build.

  python verify.py
      Live check. Triggers an execution of the workflow and asserts it reaches
      COMPLETED with the expected confirmation result. Start the worker first
      with `make start-worker`.

Messages read as an incident report. They name the symptom and point at the most
likely cause so you can trace it, rather than only printing PASS or FAIL.
"""
import argparse
import importlib.util
import os
import sys
import time
import uuid
from pathlib import Path

# The scenario input and the confirmation it must produce. verify.py triggers
# with EXPECTED_INPUT and asserts the execution returns EXPECTED_RESULT.
EXPECTED_INPUT = {"order_id": "A-1001", "customer": "Acme Robotics"}
EXPECTED_RESULT = "Order A-1001 confirmed for Acme Robotics."

# Where the workflow file lives, relative to this harness.
WORKFLOW_FILE = Path(__file__).parent / "src" / "workflows" / "confirm_order.py"

# Terminal status that means success.
TERMINAL_OK = "COMPLETED"
# Substrings that mark a terminal failure status. Confirmed against the live
# Workflows docs: terminal outcomes are COMPLETED, FAILED, CANCELED, and
# TIMED_OUT.
TERMINAL_FAIL_MARKERS = ("FAIL", "CANCEL", "TIMED_OUT")

POLL_TIMEOUT_S = 90
POLL_INTERVAL_S = 2


def load_workflow_module(soft=False):
    """Import the workflow file by path.

    The worker auto-discovers workflows by importing every file under
    src/workflows/. If this import fails, the worker would fail to register the
    workflow too, so this is the first thing to get right.

    When soft is True, a missing SDK (ModuleNotFoundError for mistralai) is
    re-raised so the caller can fall back to an offline check. All other import
    errors still fail loudly, because they are real problems in the file.
    """
    if not WORKFLOW_FILE.exists():
        fail(
            f"could not find the workflow file at {WORKFLOW_FILE}.",
            "Place confirm_order.py under src/workflows/ in your scaffolded project.",
        )
    spec = importlib.util.spec_from_file_location("confirm_order", WORKFLOW_FILE)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        sdk_missing = (exc.name or "").split(".")[0] == "mistralai"
        if soft and sdk_missing:
            raise
        fail(
            f"could not import {WORKFLOW_FILE.name}: {exc!r}.",
            "The worker discovers workflows by importing files under src/workflows/, "
            "so this same error would stop it from registering the workflow. "
            "Fix the import or syntax error shown above, then re-run.",
        )
    except Exception as exc:  # noqa: BLE001 - surface any import-time error verbatim
        fail(
            f"could not import {WORKFLOW_FILE.name}: {exc!r}.",
            "The worker discovers workflows by importing files under src/workflows/, "
            "so this same error would stop it from registering the workflow. "
            "Fix the import or syntax error shown above, then re-run.",
        )
    return module


def get_workflow_name(module):
    name = getattr(module, "WORKFLOW_NAME", None)
    if not name:
        fail(
            "WORKFLOW_NAME was not found in the workflow module.",
            "verify.py triggers by this exact name. If it differs from the name "
            "passed to @workflows.workflow.define, the trigger reports an unknown "
            "workflow. Keep both pointing at the same WORKFLOW_NAME constant.",
        )
    return name


def selftest_source_scan():
    """Offline fallback when the SDK is not installed.

    Scans the source text of confirm_order.py to confirm the workflow name is
    discoverable and the entrypoint and activity symbols exist. This runs green
    with no dependencies so the workshop frame pre-flight passes before the
    learner's project environment is set up.
    """
    source = WORKFLOW_FILE.read_text()
    name_ok = 'WORKFLOW_NAME = "confirm-order"' in source or "name=WORKFLOW_NAME" in source
    if not name_ok:
        fail(
            "the workflow name is not discoverable in confirm_order.py.",
            "verify.py triggers by this name. Keep WORKFLOW_NAME and the name= on "
            "@workflows.workflow.define pointing at the same constant.",
        )
    for symbol, note in (
        ("@workflows.workflow.define", "the workflow definition decorator"),
        ("@workflows.workflow.entrypoint", "the entrypoint decorator"),
        ("@workflows.activity(", "the activity decorator"),
    ):
        if symbol not in source:
            fail(
                f"{note} was not found in confirm_order.py.",
                "The worker discovers and registers workflows from these decorators. "
                "Restore it before building.",
            )
    print(f"  ok  workflow name is discoverable: 'confirm-order'")
    print(f"  ok  workflow, entrypoint, and activity symbols are present")


def selftest():
    print("A1 pre-flight (offline). No worker or API call is made.\n")
    try:
        module = load_workflow_module(soft=True)
    except ModuleNotFoundError as exc:
        # The SDK is not installed in this environment. Fall back to a source scan
        # so the offline pre-flight still confirms the file is wired.
        print(f"  [SKIP] live import (SDK not installed): {exc.name}")
        selftest_source_scan()
    else:
        name = get_workflow_name(module)
        print(f"  ok  workflow file imports cleanly: {WORKFLOW_FILE.name}")
        print(f"  ok  workflow name is discoverable: {name!r}")
    print(
        "\nPASS: the file is wired and the workflow name is discoverable. "
        "You are ready to build. This pre-flight does not run the workflow, so it "
        "cannot tell whether the activity returns the confirmation yet. Run "
        "`python verify.py` (with the worker started) to prove that end to end."
    )
    return 0


def make_client():
    """Build the SDK client. The API key is read from MISTRAL_API_KEY."""
    try:
        from mistralai.client import Mistral
    except Exception as exc:  # noqa: BLE001
        fail(
            f"could not import the Mistral SDK client: {exc!r}.",
            "Install it in your project with `uv add mistralai-workflows`.",
        )
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        fail(
            "MISTRAL_API_KEY is not set in the environment.",
            "Export your key (export MISTRAL_API_KEY=...) so the client and worker "
            "can authenticate against the platform.",
        )
    return Mistral(api_key=api_key)


def extract_result(execution):
    """Pull the workflow's return value off a fetched execution object.

    The execution carries its return value on `execution.result`. The worker log
    prints it as {'result': <value>}, so this also unwraps that envelope if the
    field is returned that way.
    """
    result = getattr(execution, "result", None)
    if isinstance(result, dict) and "result" in result:
        result = result["result"]
    return result


def live():
    module = load_workflow_module()
    name = get_workflow_name(module)
    client = make_client()

    # Supply our own execution_id so we can poll this exact run deterministically.
    execution_id = f"wflow-ws1-a1-{uuid.uuid4().hex[:12]}"
    print(f"A1 live check. Triggering workflow {name!r} as execution {execution_id}.")
    print(f"  input: {EXPECTED_INPUT}\n")

    try:
        execution = client.workflows.execute_workflow(
            workflow_identifier=name,
            input=EXPECTED_INPUT,
            execution_id=execution_id,
        )
    except Exception as exc:  # noqa: BLE001
        fail(
            f"the trigger was rejected for workflow {name!r}: {exc!r}.",
            "The most common cause is that no worker has registered this name yet, "
            "or the registered name differs from what was triggered. Confirm "
            "`make start-worker` is running and that its registration log lists "
            f"{name!r}, then re-run.",
        )

    print(f"  triggered (status: {getattr(execution, 'status', 'unknown')}).")

    # Poll the execution by id until it reaches a terminal status.
    status = None
    result = None
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        try:
            fetched = client.workflows.executions.get_workflow_execution(
                execution_id=execution_id
            )
        except Exception as exc:  # noqa: BLE001
            fail(
                f"could not fetch execution {execution_id}: {exc!r}.",
                "Confirm the worker is running and that the execution id was "
                "accepted at trigger time.",
            )
        status = getattr(fetched, "status", None)
        status_upper = str(status).upper() if status else ""
        is_terminal_fail = any(marker in status_upper for marker in TERMINAL_FAIL_MARKERS)
        if status == TERMINAL_OK or is_terminal_fail:
            result = extract_result(fetched)
            break
        time.sleep(POLL_INTERVAL_S)

    if status != TERMINAL_OK and any(m in str(status).upper() for m in TERMINAL_FAIL_MARKERS):
        fail(
            f"execution {execution_id} ended in a terminal failure status: {status}.",
            "The worker picked up the run but the activity or workflow raised. Read "
            "the worker log for the traceback, and remember the activity retries up "
            "to its retry_policy_max_attempts before the failure propagates.",
        )

    if status != TERMINAL_OK:
        fail(
            f"execution {execution_id} did not reach {TERMINAL_OK} within "
            f"{POLL_TIMEOUT_S}s (last status: {status}).",
            "Two common causes. (1) The worker stopped processing tasks: confirm "
            "`make start-worker` is still running. (2) confirm_order is "
            "unfinished: it still returns None, and because the activity "
            "is typed `-> str`, the platform rejects the None result and retries the "
            "workflow task, so the execution never reaches COMPLETED and sits at "
            "RUNNING. If the worker is up, complete the `# TODO` in confirm_order so "
            "the activity returns the confirmation string, then re-run.",
        )

    if result is None:
        fail(
            f"execution {execution_id} reached {TERMINAL_OK} but returned None.",
            "The worker registered the workflow and the entrypoint ran, but nothing "
            "came back. Did the activity return its value? A function that falls "
            "through returns None. Check for the TODO in confirm_order.",
        )

    if result != EXPECTED_RESULT:
        fail(
            f"execution {execution_id} reached {TERMINAL_OK} but returned "
            f"{result!r}, expected {EXPECTED_RESULT!r}.",
            "The entrypoint returned a value, so the worker-then-trigger wiring "
            "works. The activity is computing the wrong confirmation string.",
        )

    print(
        f"\nPASS: execution {execution_id} reached {TERMINAL_OK} and returned the "
        f"expected confirmation:\n  {result}"
    )
    return 0


def fail(symptom, guidance):
    print(f"\nFAIL\n  INCIDENT: {symptom}\n  TRACE IT: {guidance}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="A1 verification harness.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Offline pre-flight: import the file and confirm the workflow name is discoverable.",
    )
    args = parser.parse_args()
    if args.selftest:
        sys.exit(selftest())
    sys.exit(live())


if __name__ == "__main__":
    main()
