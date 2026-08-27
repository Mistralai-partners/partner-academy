#!/usr/bin/env python3
"""A3 verifier: interact with a running workflow (signal, query, update).

Two modes:

  python verify.py --selftest
      Offline. No API key, no worker. Proves triage_workflow.py is real,
      importable Python and that the three interaction handlers are discoverable
      by name. Use this first.

  python verify.py
      Live. Requires MISTRAL_API_KEY and a running worker (make start-worker).
      Triggers the workflow, then:
        1. sends an add_notification SIGNAL and asserts a get_status QUERY
           reflects the new notification,
        2. applies a set_priority UPDATE and asserts it RETURNS a confirmation,
        3. runs get_status again and asserts the changed priority is visible.
      State-reflects-interaction across all three is completion.

Messages read like an incident report: they name the symptom and point at the
root cause, so a failure teaches WHY, not just THAT.
"""

import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "src" / "workflows" / "triage_workflow.py"

WORKFLOW_NAME = "support_triage"
HANDLERS = ("add_notification", "get_status", "set_priority")

# Live-mode tuning.
QUERY_TIMEOUT_S = 30          # how long to wait for state to reflect an interaction
QUERY_POLL_INTERVAL_S = 1.0


def _ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def _fail(msg: str) -> str:
    print(f"  FAIL  {msg}")
    return msg


# --------------------------------------------------------------------------- #
# Selftest (offline)                                                          #
# --------------------------------------------------------------------------- #
def selftest() -> int:
    print("A3 selftest (offline)")

    if not MODULE_PATH.exists():
        _fail(
            f"triage_workflow.py not found at {MODULE_PATH}. "
            "Drop this activity into a `uvx mistralai-workflows-cli@latest setup` "
            "scaffold so the file lands under src/workflows/."
        )
        return 1

    # Prefer a real import: it proves the module loads. If the SDK is not yet
    # installed, fall back to a source scan so selftest still tells you whether
    # the handlers are declared. Both paths must find all three handler names.
    names_found = set()
    imported = False
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("triage_workflow", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        imported = True
        wf_cls = _find_workflow_class(module)
        if wf_cls is None:
            _fail(
                "no workflow class found in triage_workflow.py. Expected a class "
                f'decorated with @workflows.workflow.define(name="{WORKFLOW_NAME}").'
            )
            return 1
        for name in HANDLERS:
            if callable(getattr(wf_cls, name, None)):
                names_found.add(name)
    except ModuleNotFoundError as exc:
        if "mistralai" not in str(exc):
            raise
        print(
            "  NOTE  mistralai.workflows is not installed yet, so the module "
            "cannot be imported. Falling back to a source scan.\n"
            "        Run `uv add mistralai-workflows` before live mode."
        )
        source = MODULE_PATH.read_text(encoding="utf-8")
        for name in HANDLERS:
            if f'name="{name}"' in source or f"name='{name}'" in source:
                names_found.add(name)

    if imported:
        _ok(f"triage_workflow.py imports cleanly ({MODULE_PATH.name})")

    missing = [n for n in HANDLERS if n not in names_found]
    if missing:
        _fail(
            "these interaction handlers are not discoverable: "
            + ", ".join(missing)
            + ". Each needs a decorated handler: @signal add_notification, "
            "@query get_status, @update set_priority."
        )
        return 1

    _ok("all three handlers discoverable: " + ", ".join(HANDLERS))
    print("\nselftest GREEN. Start the worker, then run live mode: python verify.py")
    return 0


def _find_workflow_class(module):
    for obj in vars(module).values():
        if isinstance(obj, type) and all(
            hasattr(obj, name) for name in HANDLERS
        ):
            return obj
    return None


# --------------------------------------------------------------------------- #
# Live mode                                                                   #
# --------------------------------------------------------------------------- #
def _unwrap(value):
    """Return a plain dict from a query/update result.

    A query or update returns the handler's value. Depending on the SDK build
    that value may arrive as a dict, as a pydantic model, or wrapped in a small
    envelope with a `.result` field. Normalize all three so the asserts below can
    read the handler's dict directly.
    """
    if isinstance(value, dict):
        return value
    # pydantic model -> dict
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            # Some envelopes nest the handler value under "result".
            inner = dumped.get("result")
            return inner if isinstance(inner, dict) else dumped
        return dumped
    inner = getattr(value, "result", None)
    if isinstance(inner, dict):
        return inner
    return value


def _query_status(client, execution_id: str) -> dict:
    result = client.workflows.executions.query_workflow_execution(
        execution_id=execution_id, name="get_status"
    )
    return _unwrap(result)


def live() -> int:
    print("A3 live verification")

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        _fail(
            "MISTRAL_API_KEY is not exported. Live mode drives a real execution; "
            "export the key, then `make start-worker` in another terminal."
        )
        return 1

    try:
        from mistralai.client import Mistral
    except ImportError:
        _fail(
            "mistralai is not installed. Run `uv add mistralai-workflows` inside "
            "the scaffold, then retry."
        )
        return 1

    client = Mistral(api_key=api_key)

    # --- Trigger the long-running workflow ---------------------------------- #
    try:
        execution = client.workflows.execute_workflow(
            workflow_identifier=WORKFLOW_NAME,
            input={"case_id": "CASE-1001"},
        )
    except Exception as exc:  # noqa: BLE001 - report any startup failure plainly
        _fail(
            f"could not start the '{WORKFLOW_NAME}' workflow: {exc}. Is the worker "
            "running (make start-worker) and does @define(name=...) match?"
        )
        return 1

    execution_id = execution.execution_id
    _ok(f"started execution {execution_id} (status={execution.status})")

    # --- 1) SIGNAL, then assert the QUERY reflects it ----------------------- #
    signal_message = "customer replied, awaiting triage"
    try:
        client.workflows.executions.signal_workflow_execution(
            execution_id=execution_id,
            name="add_notification",
            input={"message": signal_message, "priority": 2},
        )
    except Exception as exc:  # noqa: BLE001
        _fail(
            f"the add_notification signal was rejected: {exc}. A 422 here means the "
            "payload did not match the handler's declared params (message: str, "
            "priority: int)."
        )
        return 1

    deadline = time.time() + QUERY_TIMEOUT_S
    reflected = False
    last_status: dict | None = None
    while time.time() < deadline:
        try:
            last_status = _query_status(client, execution_id)
        except Exception as exc:  # noqa: BLE001
            _fail(
                f"get_status query failed: {exc}. If the workflow is busy-looping "
                "with no wait_condition, the query cannot get a turn to run."
            )
            return 1
        if last_status.get("notification_count", 0) >= 1:
            reflected = True
            break
        time.sleep(QUERY_POLL_INTERVAL_S)

    if not reflected:
        _fail(
            "query returned stale state after the signal: notification_count is "
            f"still 0 ({QUERY_TIMEOUT_S}s elapsed). Did the workflow wait_condition "
            "on the change, or is it busy-looping past it? A signal that lands but "
            "never wakes the loop leaves the case history invisible to the "
            "dashboard. Root cause is in the entrypoint's wait, not in the signal."
        )
        return 1
    _ok(
        "signal reflected: get_status shows notification_count="
        f"{last_status.get('notification_count')}"
    )

    # --- 2) UPDATE returns a confirmation ----------------------------------- #
    new_priority = 4
    try:
        confirmation = client.workflows.executions.update_workflow_execution(
            execution_id=execution_id,
            name="set_priority",
            input={"priority": new_priority},
        )
    except Exception as exc:  # noqa: BLE001
        _fail(
            f"the set_priority update failed or returned nothing: {exc}. An update "
            "must return a value; if you stubbed it (NotImplementedError) or wired "
            "it as a signal, the caller gets no confirmation back."
        )
        return 1

    conf = _unwrap(confirmation)
    if not isinstance(conf, dict) or conf.get("priority") != new_priority:
        _fail(
            "the update did not return a usable confirmation. Expected a value that "
            f"reports the new priority ({new_priority}); got: {conf!r}. Use an "
            "update (not a signal) when the caller needs a confirmed result."
        )
        return 1
    _ok(f"update returned confirmation: {conf}")

    # --- 3) Follow-up QUERY shows the changed priority ---------------------- #
    try:
        final_status = _query_status(client, execution_id)
    except Exception as exc:  # noqa: BLE001
        _fail(f"follow-up get_status query failed: {exc}.")
        return 1

    if final_status.get("priority") != new_priority:
        _fail(
            "state does not reflect the update: get_status still reports priority="
            f"{final_status.get('priority')}, expected {new_priority}. The update "
            "returned a confirmation but did not durably mutate self.priority."
        )
        return 1
    _ok(f"query confirms mutated state: priority={final_status.get('priority')}")

    print("\nGREEN. State reflected the signal, the query stayed read-only, and the "
          "update both returned a confirmation and changed the case priority.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="A3 verifier")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="offline structural check (no API key, no worker)",
    )
    args = parser.parse_args()
    return selftest() if args.selftest else live()


if __name__ == "__main__":
    sys.exit(main())
