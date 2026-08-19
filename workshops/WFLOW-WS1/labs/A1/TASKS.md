# A1: Build and Run Your First Durable Workflow

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

- **Activity code:** WFLOW-WS1-A1 (first-workflow) | **Time:** 30 min | **Level:** Apply

## What you will build

- An ISV is prototyping an order-confirmation step that must run reliably even if
the process restarts. You will scaffold a fresh Workflows project, define a
workflow whose single activity computes the confirmation, run the worker,
trigger an execution, and prove it completes with the expected result.

- This activity builds two behaviors:

- **B1:** scaffold, define, run, and verify a durable workflow with one activity.
- **B5:** apply safe durability defaults on the activity (a bounded timeout and
  a retry policy).

- The mental model to hold: the **workflow orchestrates**, and the **activity does
the work and holds any side effects**. In this lab the activity computes the
confirmation, and the entrypoint awaits it and returns the result.

## Prerequisites

- Python 3.12 or later, and the uv package manager (uvx ships with uv).
- A Mistral account and an API key from console.mistral.ai.
- `MISTRAL_API_KEY` exported in the terminal you will use.

## Setup (budget: 5 minutes or less)

- Scaffold a fresh project:

   ```bash
   uvx mistralai-workflows-cli@latest setup
   ```

- Accept the default project name (`my-workflow`) and paste your API key when
   prompted. This creates the SDK-configured project, an example workflow at
   `src/workflows/hello.py`, a worker that auto-discovers workflows under
   `src/workflows/`, and a `Makefile`.

- Copy this activity's files into the scaffold:
   - `starter/src/workflows/confirm_order.py` into the project's `src/workflows/`.
   - `starter/verify.py` into the project root.

- Confirm the wiring before you edit anything:

   ```bash
   python verify.py --selftest
   ```

- Green means the file imports and the workflow name is discoverable. You are
   ready to build.

- **Done when:** the live check passes. That is, `python verify.py` reports the
execution reached `COMPLETED` and returned the expected confirmation. Two things
must hold: correct status and correct result.

## Tasks (easy to hard)

### Task 1: Read the workflow and confirm the pre-flight

- **Objective:** *Identify* the workflow, its activity, and the input model in
  `confirm_order.py`, and run the offline pre-flight.
- **Scenario:** Before changing code you inherited, you confirm what is wired and
  what is missing. On the job, a green pre-flight tells you the environment is
  ready so a later failure points at your change, not your setup.
- **Hint (evidence, not fix):** `python verify.py --selftest` should pass on the
  untouched starter. Read the output: it tells you the file imports and names the
  identifier you will trigger against. Note that it explicitly says it has not
  run the workflow yet.
- **Acceptance:** the pre-flight prints PASS and echoes the workflow name.

### Task 2: Complete the activity

- **Objective:** *Apply* the durable-workflow pattern by returning the
  confirmation from the single activity.
- **Scenario:** The order-confirmation logic is the side-effecting work, so it
  belongs in an activity, never in the workflow body. This is the one place the
  confirmation should be computed.
- **Hint (evidence, not fix):** find the `# TODO` in `confirm_order`. The
  function currently falls through, so it hands back nothing. The activity's type
  hint (`-> str`) and the expected result in `verify.py` tell you the exact shape
  the confirmation must take.
- **Acceptance:** the live check no longer reports a `None` result once the worker
  runs the workflow (see Task 4).

### Task 3: Start the worker

- **Objective:** *Run* the worker so it registers the workflow and waits for
  tasks.
- **Scenario:** A trigger has nowhere to go until a worker has registered the
  workflow name. Always start the worker first.
- **Hint (evidence, not fix):** from the project root, run `make start-worker` and
  read its startup log. It lists the workflows it discovered under
  `src/workflows/`. Confirm `confirm-order` appears there. Leave this terminal
  running.
- **Acceptance:** the worker log shows `confirm-order` registered and the worker
  is waiting for tasks.

### Task 4: Trigger an execution and verify

- **Objective:** *Verify* the workflow by triggering an execution and checking its
  final status and result, not the worker log scroll-by.
- **Scenario:** The log tells you an activity ran; only the execution's terminal
  status and result tell you it produced the right answer. Verifying against
  status plus result is what you would trust in production.
- **Hint (evidence, not fix):** in a second terminal, run `python verify.py`. If
  the trigger is rejected, the incident report points at worker registration or a
  name mismatch: cross-check the name in the worker's startup log against
  `WORKFLOW_NAME`. You can also trigger by hand to compare:

  ```bash
  make execute workflow=confirm-order input='{"order_id": "A-1001", "customer": "Acme Robotics"}'
  ```

- The worker log then shows a line like `Result: {'result': ...}`.
- **Acceptance:** `python verify.py` prints PASS with the execution reaching
  `COMPLETED` and returning the expected confirmation.

## Best practices and pitfalls

- **Put every side effect inside an activity, never the workflow body.** The
  workflow orchestrates; the activity does the work. This keeps the workflow
  replayable and durable.
- **The `name` in `@workflow.define` is the identifier you trigger and schedule
  against.** Keep it stable and keep it matching what you trigger. This lab uses a
  single `WORKFLOW_NAME` constant so both stay in sync.
- **Always start the worker before triggering, and confirm it registered the
  workflow.** Read the startup log rather than assuming.
- **Verify against execution status plus result, not the worker log scroll-by.**
  A log line proves an activity ran; the terminal status and result prove it ran
  correctly.
- **Common failure:** the worker starts but the trigger reports the workflow is
  unknown. The file was not discovered under `src/workflows/`, or the triggered
  name differs from the registered name. Trace it from the worker's registration
  output, not by guessing.
- **Safe durability defaults (B5):** the activity sets `start_to_close_timeout`
  so an unresponsive activity cannot block forever, and a retry policy so a
  transient failure retries with growing backoff. Because retries re-run the
  activity, the same input must always produce the same result.

## Stretch

- Add a second activity (for example, one that formats a customer-facing receipt
line from the confirmation) and chain it in the entrypoint: `await` the first
activity, then pass its result into the second. Re-run and confirm both
activities appear, in order, in the execution history at console.mistral.ai.

## What you learned and where to go next

- You scaffolded a project, defined a workflow with one activity, applied safe
durability defaults, ran a worker, triggered an execution, and verified it
against status and result. That is the whole loop you will repeat for every
workflow: define, register with a worker, trigger by name, verify.

- Next, deepen these foundations:

- **WFLOW-200** goes further on activity configuration, determinism, signals,
  queries, and updates.
- **WFLOW-300** covers production patterns such as scheduling, child workflows,
  observability, and error handling.
