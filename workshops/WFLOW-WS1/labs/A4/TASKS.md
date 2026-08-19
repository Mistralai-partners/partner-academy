# A4: Diagnose a Nondeterminism Failure in a Scheduled Workflow

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

- **Activity code:** WFLOW-WS1-A4 (determinism-debug)
- **Time:** 45 minutes

- **Complexity:** Complex (L300 debug plus schedule wiring)
- **Builds on skills:** B4, B5, B1

## The scenario

- A team put a nightly reconciliation workflow on a schedule. It reconciles a group
of account IDs against the ledger, and it passed every manual run during
development. After it went on the schedule it began to fail on replay with a
nondeterminism error, and only sometimes. Some nights it completes. Some nights it
diverges partway through.

- Your job is to reproduce the failure, trace it to the offending call in the
workflow body, move the side effect behind an activity boundary (or a
deterministic helper), keep the body deterministic including a second, quieter
trap, then complete and attach the schedule so the run fires on its own.

## Why this happens (concept in context)

- The platform recovers a workflow by REPLAYING its history. It re-runs the workflow
body and expects the same command sequence it recorded the first time. So the
workflow body must be deterministic: the same inputs must produce the same
sequence of commands. Any call that reads wall-clock time, draws randomness,
touches the network or filesystem, or iterates an unordered collection can return
a different value on the second run and make replay diverge.

- Work like that belongs in an ACTIVITY (activity results are recorded and replayed
from history, not re-run), or must use a deterministic helper: `workflow.now()`
instead of `datetime.now()`, `workflow.uuid4()` instead of `uuid.uuid4()`,
`workflow.random()` instead of `random.random()`. Determinism enforcement is on by
default; a sandbox intercepts the unsafe calls and raises at the call site.

- Scheduling is declared on the workflow with `@workflow.define(schedules=[...])`.
The worker registers the schedule with the platform at startup, so a schedule
change takes effect only after you restart the worker.

## Prerequisites

- Python 3.12+ and `uv`.
- `MISTRAL_API_KEY` exported.
- A workflows scaffold created with `uvx mistralai-workflows-cli@latest setup` and
  `uv add mistralai-workflows`.
- The A4 starter files.

## Setup (under 5 minutes)

- Create a scaffold if you do not have one: `uvx mistralai-workflows-cli@latest setup`.
- Copy the A4 starter `src/workflows/reconciliation.py` and
   `src/workflows/schedule.py` into the scaffold's `src/workflows/`. Copy
   `verify.py` to the scaffold root.
- Confirm discovery: `uv run python verify.py --selftest`. Expect it to FAIL with
   a determinism report and a schedule report. That failure is your starting
   point.

## Done when

- `uv run python verify.py --selftest` prints `[PASS]` for all three checks
(imports, determinism static scan, schedule shape), and the live run in Task 5
completes with no nondeterminism error while the schedule is registered.

---

## Task 1: Reproduce the nondeterminism failure

- **Objective:** Reproduce the intermittent replay failure so you are
  debugging observed behavior, not a guess.
- **Scenario:** The workflow passes some runs and fails others. You need to see it
  fail before you change anything.
- **Steps:** Start the worker (`make start-worker`) and trigger the workflow:
  `make execute workflow=reconciliation-workflow input='{"account_ids":["acct-001","acct-002","acct-003"]}'`.
  Run it several times and watch the run at console.mistral.ai. Also run
  `uv run python verify.py --selftest` and read the determinism report.
- **Hint (evidence, not fix):** A determinism bug can pass a single happy run and
  fail on replay or recovery. Do not trust one green run. The console shows the
  nondeterminism error together with the step index where replay diverged.
- **Acceptance:** You can point to the replay error and the divergent step index,
  and the selftest determinism check is red.

## Task 2: Trace the failure to the offending call

- **Objective:** Locate the exact lines in the workflow body that break
  replay, using the replay evidence rather than a top-to-bottom re-read.
- **Scenario:** Two lines in `reconciliation.py` carry a `# BUG:` marker. One is
  loud, one is quiet.
- **Steps:** Map the console's divergent step index back to a line in the
  entrypoint. Note what each `# BUG:` line does: one reads wall-clock time, one
  iterates a collection.
- **Hint (evidence, not fix):** Ask of each suspect line: would this produce the
  same value on a second run of the same body? Wall-clock time changes every call.
  A `set` has no defined iteration order, so the loop can visit accounts in a
  different order on replay. That reordering is why the failure is intermittent,
  not constant.
- **Acceptance:** You can name both offending constructs and explain, for each,
  why replay diverges.

## Task 3: Keep the workflow body deterministic

- **Objective:** Decide where each side effect belongs and make the body
  pure orchestration, including the quiet iteration trap.
- **Scenario:** The body must orchestrate only. Time, randomness, network,
  filesystem, and unordered iteration do not belong here.
- **Steps:** Relocate the wall-clock read so it no longer runs live in the body
  (use the deterministic time helper, or compute it in an activity and await the
  result). Then make the account iteration deterministic so replay visits accounts
  in the same order every time.
- **Hint (evidence, not fix):** A common near-miss fixes the loud line and leaves
  the unordered iteration in place, so replay still diverges intermittently. Trace
  from the replay error's step index, not by re-reading top to bottom. The
  workflow body should read like pure orchestration when you are done.
- **Acceptance:** `uv run python verify.py --selftest` shows the determinism check
  `[PASS]`; the entrypoint no longer reads wall-clock time or iterates an
  unordered collection.

## Task 4: Complete and attach the schedule

- **Objective:** Turn the incomplete schedule stub into a valid,
  attached schedule so the workflow fires on its own.
- **Scenario:** `schedule.py` builds a `ScheduleDefinition`, but it has no trigger
  and no input, and nothing attaches it to the workflow.
- **Steps:** Complete `build_schedule_definition()` with a `cron_expressions`
  trigger (5-field, UTC), the workflow `input`, and a deliberate overlap and
  catchup policy. Then attach the exported `SCHEDULE` to the workflow with
  `@workflow.define(..., schedules=[SCHEDULE])`.
- **Hint (evidence, not fix):** A schedule that is defined but never attached never
  fires; the worker reads schedules from the decorator at startup. Set the overlap
  policy on purpose (default is `SKIP`; others are `BUFFER_ONE`, `ALLOW_ALL`).
  Cron is converted server-side, so calendars are the recommended native form when
  you need them.
- **Acceptance:** `uv run python verify.py --selftest` shows the schedule-shape
  check `[PASS]` (well-formed definition with a trigger and input, attached via
  `schedules=`).

## Task 5: Run the worker and verify end to end

- **Objective:** Confirm both success conditions together on a live run.
- **Scenario:** Green means the determinism check passes AND the schedule is
  registered.
- **Steps:** Restart the worker so it re-reads the schedule (`make start-worker`).
  Trigger a run or let the schedule fire, and watch it at console.mistral.ai. Run
  `uv run python verify.py` and read the live guidance.
- **Hint (evidence, not fix):** A schedule change takes effect only after a worker
  restart. Green = the run completes with no nondeterminism error on replay and
  the workflow appears with its schedule registered.
- **Acceptance:** The live run completes cleanly and the schedule is registered;
  all three selftest checks are `[PASS]`.

---

## Best practices and pitfalls

- **Treat the workflow body as pure orchestration.** Any time, randomness,
   network, filesystem, or unordered-collection access belongs in an activity or a
   deterministic helper, never in the body.
- **Do not trust one green run.** A determinism bug can pass locally and fail on
   replay or recovery. Always run the determinism check.
- **Set schedule policies deliberately.** Prefer calendars when you need native
   scheduling (cron is converted server-side). Choose the overlap and catchup
   policy on purpose rather than accepting defaults by accident.
- **Attach the schedule and restart the worker.** The worker registers schedules
   from the decorator at startup; a definition that is not attached, or a change
   made without a restart, never takes effect.
- **Watch the quiet trap.** The classic near-miss fixes the wall-clock line but
   leaves an unordered `set` iteration in the body, so replay still diverges
   intermittently. Trace from the replay error's step index.

## Stretch

- Replace the schedule trigger with a child (sub-)workflow: have the parent start
and await a child with `execute_workflow(ChildWorkflow, params=...)`. Then reason
about a long-lived scheduled run whose history keeps growing: when would you need
`continue_as_new` to keep the replay history bounded, and what state would you
carry across the boundary? Write two or three sentences arguing when the history
size, not the logic, forces `continue_as_new`.

## What you learned and where to go next

- You reproduced an intermittent replay failure, traced it from the divergent step
index to the offending calls, moved the side effects to where the platform can
replay them safely, kept the body deterministic through the quiet iteration trap,
and attached a schedule the worker registers at startup.

- Next: **WFLOW-300** goes deeper on durable execution, replay, and recovery, and
**WFLOW-400** on production operations and scale. Both feed the Mistral Workflows
certification.
