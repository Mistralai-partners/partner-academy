# A2 - Make It Resilient: Timeouts, Retries, and Heartbeats

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

- WFLOW-WS1-A2 - resilient-activity - 40 minutes

## What you will build

- You will take an order confirmation activity that calls a flaky downstream
service and make the execution self-heal. By the end, a single execution
survives an injected fault that both errors and hangs, and it still reaches
COMPLETED.

## Prerequisites

- A workflows scaffold created with `uvx mistralai-workflows-cli@latest setup`.
- Python 3.12+ and `uv`.
- `MISTRAL_API_KEY` exported in your shell.
- You can run `make start-worker` and `make execute` from the scaffold root.

- This activity is self-contained. It has its own scenario, its own setup, and
its own verifier. It does not depend on any other activity in the workshop.

## Setup (under 5 minutes)

- Create or reuse a scaffold: `uvx mistralai-workflows-cli@latest setup`.
- Copy the A2 starter files into it:
   - `starter/src/workflows/resilient_confirm.py` into the scaffold's
     `src/workflows/`.
   - `starter/verify.py` into the scaffold root (next to the Makefile).
- If the SDK is not already present, add it: `uv add mistralai-workflows`.
- Export your key: `export MISTRAL_API_KEY=...`.
- Prove the file is wired up before running a worker:
   `python verify.py --selftest`.

## Done when

- All of these pass:

- `python verify.py --selftest` is green (the module imports and the workflow
   name is discoverable).
- A worker is running with `resilient_confirm` loaded.
- `python verify.py` is green: the execution reaches COMPLETED and did so via
   retry (more than one attempt) against the injected fault.

---

## Tasks

- Work top to bottom. Each task builds on the one before it.

### Task 1 - Read the scenario, do not fix it yet

- Objective: Identify how the injected fault behaves across
  attempts.
- Scenario: `resilient_confirm.py` ships a provided fault injector,
  `_flaky_downstream_confirm`. It is the downstream service, not a bug.
- Hint: Look at what happens on the first attempts versus the attempt after
  that. Notice that attempt state is kept on disk keyed by `request_id`, so a
  retry advances the fault instead of resetting it. Do not remove or edit the
  injector or the loop logic.
- Acceptance: You can state, in one sentence, the two different ways this
  service misbehaves and which one a plain retry alone will not solve.

### Task 2 - Prove the failure

- Objective: Run the starter as-is and observe the failure mode.
- Scenario: The activity is a bare `@workflows.activity()` with no durability
  configuration.
- Hint: Start the worker (`make start-worker`), then run `python verify.py`.
  Watch the worker log and the verifier's incident report. Do not read the fix
  from the verifier; read the evidence it points at.
- Acceptance: The verifier fails and tells you whether the run hung or failed,
  and why.

### Task 3 - Bound and retry each attempt

- Objective: Configure the activity so a transient failure is retried
  and no single attempt can run forever.
- Scenario: The first attempts raise a transient error. Today that error kills
  the execution.
- Hint: The decorator accepts `start_to_close_timeout`,
  `retry_policy_max_attempts`, and `retry_policy_backoff_coefficient`. Choose a
  `max_attempts` that outlasts how many times the fault misbehaves before it
  succeeds. Choose the values deliberately; do not paste a default.
- Acceptance: The transient failures no longer end the execution. It now gets
  as far as the hang.

### Task 4 - Catch the hang fast

- Objective: Detect the wedged attempt in seconds instead of waiting out
  the full timeout.
- Scenario: One attempt accepts the call and then wedges. It never returns on
  its own.
- Hint: Add a `heartbeat_timeout` that is much shorter than how long the wedge
  lasts. Then make the healthy work loop call `workflows.activity_heartbeat(...)` on every
  iteration so a slow-but-healthy loop is not mistaken for a wedged one. The
  loop already marks where the liveness signal belongs.
- Acceptance: The wedged attempt is given up on quickly and retried, and the
  healthy loop is not falsely killed.

### Task 5 - Verify recovery via retry

- Objective: Prove the execution recovered because of config, not luck.
- Scenario: The verifier triggers the execution against a fresh, re-armed fault.
- Hint: Run `python verify.py`. Green requires COMPLETED AND more than one
  attempt. A one-attempt success would mean the fault never fired.
- Acceptance: `python verify.py` is green with an attempt count greater than 1.

---

## Best practices and pitfalls

- Every activity that can hang needs a `start_to_close_timeout`. An unbounded
  activity can block indefinitely and there is nothing to fail over from.
- Set `retry_policy_max_attempts` and the backoff coefficient deliberately, not
  by copying a default. They bound the blast radius when a dependency is truly
  broken, so retries eventually stop instead of hammering forever.
- Heartbeat any long-running activity. `heartbeat_timeout` lets a hang be caught
  within seconds rather than at the full `start_to_close_timeout`. Heartbeats
  are not supported for local activities.
- Keep activities idempotent. A retry re-runs the whole activity, so its side
  effects must converge to the same observable state. Here the confirmation is
  derived only from `order_id`, so repeating it is safe.
- Common failure: a retry policy is set but the activity is not idempotent, so
  each retry double-applies the side effect. You trace it from the duplicated
  result. Remember the whole activity is the retry unit: a nested call does not
  retry on its own, it replays the entire outer activity from the top. Compose
  at the workflow level when you need per-step retry isolation.

---

## Stretch

- Lower `retry_policy_max_attempts` below what the fault needs. Before you run,
   predict the exact failure mode and which attempt it dies on. Then run and
   confirm your prediction against the verifier's report.
- Now reason about the hang specifically. Suppose you kept a generous retry
   budget but tried to fix the wedge by only raising `start_to_close_timeout`,
   with no heartbeat. Explain why that would not help, and would in fact make
   the wedge worse. Point to what actually detects a silent, wedged attempt and
   why that detector, not a bigger timeout, is the fix.

---

## What you learned

- You made an activity survive a downstream that both errors and hangs, using
`start_to_close_timeout`, a deliberate retry policy with exponential backoff,
and `heartbeat_timeout` plus periodic `workflows.activity_heartbeat(...)` calls. You also
proved recovery happened via retry rather than luck, and you reasoned about why a
bigger timeout is not a substitute for a heartbeat.

- Next: A3 continues the resilient confirmation story. See the A3 lab folder.
