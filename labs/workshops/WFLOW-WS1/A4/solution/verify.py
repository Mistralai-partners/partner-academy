#!/usr/bin/env python
"""A4 verifier: verify-as-incident-report.

Two modes:

 uv run python verify.py --selftest # offline: import + static determinism scan + schedule shape
 uv run python verify.py # live: run the workflow through replay + confirm the schedule

Green for A4 means BOTH of these hold:
 1. The determinism check passes: no nondeterminism error surfaces on replay.
 2. The workflow declares a valid schedule (a well-formed ScheduleDefinition
 with a cron trigger and input, attached via @workflow.define(schedules=[...]))
 that the worker registers at startup.

The messages below are written like an incident report: they name the offending
call and point at the replay step index concept, not the fix. When a check fails,
read the message, open the named file, and reason about which line reads
wall-clock time or iterates an unordered collection.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RECONCILIATION_PY = SRC / "workflows" / "reconciliation.py"
SCHEDULE_PY = SRC / "workflows" / "schedule.py"

# Calls and constructs that break replay when they run in the workflow body.
# Substring form, checked only within the entrypoint body (activities may use
# these legitimately).
NONDETERMINISTIC_MARKERS = {
    "datetime.now(": "reads wall-clock time",
    "time.time(": "reads wall-clock time",
    "random.random(": "draws randomness",
    "random.choice(": "draws randomness",
    "uuid.uuid4(": "draws a random UUID",
    "set(": "iterates or builds an unordered collection",
    "open(": "touches the filesystem",
    "os.environ": "reads process environment",
}


class CheckError(Exception):
    """A verification check failed. The message is the incident report."""


class CheckSkipped(Exception):
    """A check could not run offline (needs the SDK). Not a failure."""


def _entrypoint_body_source() -> str:
    """Return the source of the workflow entrypoint method only.

    Scanning just the entrypoint body keeps the determinism check honest:
    activities are allowed to read the clock or the network, the workflow body
    is not.
    """
    tree = ast.parse(RECONCILIATION_PY.read_text())
    lines = RECONCILIATION_PY.read_text().splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorated = any(
                    "entrypoint" in ast.unparse(dec) for dec in item.decorator_list
                )
                if decorated:
                    start = item.lineno - 1
                    end = item.end_lineno
                    return "\n".join(lines[start:end])
    raise CheckError(
        "no workflow entrypoint found in "
        f"{RECONCILIATION_PY.name}: the determinism scan needs a method decorated "
        "with @workflow.entrypoint inside the @workflow.define class."
    )


def _workflow_name_from_source() -> str | None:
    """Read the WORKFLOW_NAME constant from source without importing the SDK."""
    tree = ast.parse(RECONCILIATION_PY.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "WORKFLOW_NAME":
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        return node.value.value
    return None


def check_imports() -> None:
    """The lab files must import cleanly once the SDK is installed.

    This is the only check that needs a live SDK. When mistralai.workflows is not
    installed (for example a pre-flight in a bare environment) it is skipped, not
    failed: the determinism scan and the schedule-shape check still run against
    source text, so the selftest stays meaningful offline.
    """
    try:
        importlib.import_module("mistralai.workflows")
    except ModuleNotFoundError:
        # SDK absent: the lab modules cannot import. Validate what source allows.
        if not _workflow_name_from_source():
            raise CheckError(
                "reconciliation.py does not define a WORKFLOW_NAME string constant: "
                "the schedule and the verifier read it to trigger the right workflow."
            )
        raise CheckSkipped(
            "mistralai.workflows is not installed, so the live import is skipped. "
            "The static checks below still run against source. Install with "
            "`uv add mistralai-workflows` to enable the live import and run."
        )
    # SDK present: import the lab modules for real.
    try:
        recon = importlib.import_module("workflows.reconciliation")
        importlib.import_module("workflows.schedule")
    except Exception as exc: # noqa: BLE001 (report any import failure)
        raise CheckError(f"a lab file failed to import: {exc!r}") from exc
    if not getattr(recon, "WORKFLOW_NAME", None):
        raise CheckError(
            "workflows.reconciliation is missing WORKFLOW_NAME: the schedule and "
            "the verifier both read this constant to trigger the right workflow."
        )


def check_determinism_static() -> None:
    """Offline determinism check: flag replay-breaking calls in the body.

    This is the check that would have caught the bug before it ever reached a
    schedule. A single happy run can pass while replay diverges, so do not trust
    one green run: trust this scan and the live replay below.
    """
    body = _entrypoint_body_source()
    hits = [
        f" - `{marker}` in the workflow body {why}"
        for marker, why in NONDETERMINISTIC_MARKERS.items()
        if marker in body
    ]
    if hits:
        raise CheckError(
            "replay would diverge: the workflow body contains calls that produce a\n"
            "different value on the second run. On replay the platform re-runs this\n"
            "body and expects the recorded command sequence; these lines break that.\n"
            "Offending constructs found in the entrypoint of "
            f"{RECONCILIATION_PY.name}:\n"
            + "\n".join(hits)
            + "\n\nMove the side effect out of the workflow body (into an activity, or\n"
            "use a deterministic helper such as workflow.now), and iterate a\n"
            "stable, ordered collection instead of an unordered one."
        )


def _decorator_declares_schedules() -> bool:
    """True if the workflow @workflow.define(...) passes a schedules= argument."""
    tree = ast.parse(RECONCILIATION_PY.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and "define" in ast.unparse(dec.func):
                if any(kw.arg == "schedules" for kw in dec.keywords):
                    return True
    return False


def _is_nonempty_literal(node: ast.expr) -> bool:
    """False only for an empty list/dict/set/tuple literal; True otherwise."""
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return len(node.elts) > 0
    if isinstance(node, ast.Dict):
        return len(node.keys) > 0
    return True


def _schedule_definition_kwargs() -> dict[str, ast.expr]:
    """Return the keyword args of the ScheduleDefinition(...) built in schedule.py.

    Source-based so the check runs offline. Raises CheckError if the builder does
    not construct a ScheduleDefinition at all.
    """
    tree = ast.parse(SCHEDULE_PY.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name == "build_schedule_definition"
        ):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and ast.unparse(sub.func).endswith(
                    "ScheduleDefinition"
                ):
                    return {kw.arg: kw.value for kw in sub.keywords if kw.arg}
    raise CheckError(
        f"build_schedule_definition in {SCHEDULE_PY.name} does not construct a "
        "ScheduleDefinition. It must return a ScheduleDefinition(...) with a trigger "
        "and input."
    )


def check_schedule_shape() -> None:
    """The workflow must declare a schedule that carries a trigger and input.

    Scheduling is declared on the workflow with @workflow.define(schedules=[...]);
    the worker registers it at startup (a change needs a worker restart). This
    check reads source only, so it runs offline: it confirms the ScheduleDefinition
    is well formed and actually attached.
    """
    kwargs = _schedule_definition_kwargs()

    triggers = [
        key
        for key in ("cron_expressions", "calendars", "intervals")
        if key in kwargs and _is_nonempty_literal(kwargs[key])
    ]
    if not triggers:
        raise CheckError(
            "the ScheduleDefinition has no trigger: set at least one "
            "cron_expressions entry (5-field, UTC), or the schedule never fires."
        )
    if "input" not in kwargs or not _is_nonempty_literal(kwargs["input"]):
        raise CheckError(
            "the ScheduleDefinition has no input: the scheduled run needs the "
            "account_ids payload the workflow entrypoint expects."
        )
    if not _decorator_declares_schedules():
        raise CheckError(
            "the schedule is defined but never attached: no schedules= argument on "
            f"@workflow.define in {RECONCILIATION_PY.name}. The worker registers "
            "schedules from the decorator at startup, so an unattached definition "
            "never fires. Wire it with @workflow.define(..., schedules=[SCHEDULE]) "
            "and restart the worker."
        )


def run_selftest() -> int:
    checks = (
        ("imports", check_imports),
        ("determinism (static scan)", check_determinism_static),
        ("schedule shape", check_schedule_shape),
    )
    failures = 0
    skipped = 0
    for name, fn in checks:
        try:
            fn()
        except CheckSkipped as exc:
            skipped += 1
            print(f"[SKIP] {name}\n{exc}\n")
        except CheckError as exc:
            failures += 1
            print(f"[FAIL] {name}\n{exc}\n")
        else:
            print(f"[PASS] {name}")
    if failures:
        print(f"\n{failures} check(s) failed. Fix the workflow body and the schedule, "
              "then re-run.")
        return 1
    note = " (live import skipped; install the SDK to enable it)" if skipped else ""
    print(f"\nSelftest green: body scans clean and the schedule is well formed{note}. "
          "Run the live check next.")
    return 0


def run_live() -> int:
    """Live check: run the workflow through replay and confirm the schedule.

    [VERIFY] The exact mechanism to force a replay from a test harness (for
    example restarting the worker mid-execution, or a replay-from-history entry
    point) is not named in the live docs. Confirmed execution surface you can use
    to drive a run: `client.workflows.execute_workflow(workflow_identifier=...,
    input=...)`, poll `client.workflows.executions.get_workflow_execution(
    execution_id=...).status`, or watch `client.workflows.events.get_stream_events(
    workflow_exec_id=...)` for a WORKFLOW_EXECUTION_COMPLETED event. The console at
    console.mistral.ai shows a nondeterminism error with its divergent step index.
    """
    print(
        "[VERIFY] live replay is not fully grounded from a harness. To verify live today:\n"
        " 1. Start the worker: make start-worker\n"
        " The worker registers the workflow's schedule at startup. A schedule\n"
        " change takes effect only after a worker RESTART.\n"
        " 2. Trigger a run now (or let the schedule fire):\n"
        " make execute workflow=reconciliation-workflow input='{\"account_ids\":[\"acct-001\",\"acct-002\"]}'\n"
        " 3. Open console.mistral.ai. Green = the run completes with NO nondeterminism\n"
        " error on replay, AND the workflow appears with its schedule registered.\n"
        " A red run names the divergent step index; map that step back to the line\n"
        " in the workflow body that read the clock or iterated an unordered\n"
        " collection.\n"
        "[VERIFY] Asserting the schedule's next-fire time from the harness is not\n"
        "grounded (schedule next-fire is managed platform-side; the REST API is the\n"
        "documented path for independent schedule management)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="A4 verifier")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="offline: import + static determinism scan + schedule shape",
    )
    args = parser.parse_args()
    return run_selftest() if args.selftest else run_live()


if __name__ == "__main__":
    raise SystemExit(main())
