# A3 - Interact With a Running Workflow: Signals, Queries, Updates

- **Code:** WFLOW-WS1-A3 (interact-workflow) - **Time:** 35 min - **Complexity:** Complex

## What you will build

- A support-triage workflow runs for the life of a case. Three different needs
hit it while it runs, and each need wants a different interaction primitive:

- **Notifications arrive over time.** The sender does not wait for a reply. This
  is fire-and-forget, so it is a **signal**.
- **A dashboard must read current status** without disturbing the case. A read
  that never changes state is a **query**.
- **An agent changes the case priority and needs a confirmation back.** A call
  that mutates state and returns a result is an **update**.

- You wire the right primitive to each need and prove the workflow's state
reflects every interaction.

### Behavior when done

- `add_notification` is a signal: it appends a notification and the workflow
  **wakes** to react, without busy-looping.
- `get_status` is a query: synchronous, read-only, and it **never** mutates state.
- `set_priority` is an update: it mutates the priority, optionally runs a small
  activity, and **returns a confirmation** the caller reads synchronously.

### Prerequisites

- Python 3.12+ and `uv`.
- `MISTRAL_API_KEY` exported in your shell.
- A scaffold from `uvx mistralai-workflows-cli@latest setup` with
  `uv add mistralai-workflows` already run. Setup should take under 5 minutes.

### Done when

- Four checks pass:

- `python verify.py --selftest` is green (file imports, three handlers found).
- A signal is reflected by a follow-up query.
- An update returns a confirmation.
- A follow-up query shows the changed priority.

---

## Setup (under 5 minutes)

- Create a scaffold if you do not have one:
   `uvx mistralai-workflows-cli@latest setup`, then `uv add mistralai-workflows`.
- Copy this activity's files into the scaffold so `triage_workflow.py` lands in
   `src/workflows/` and `verify.py` sits at the scaffold root. The worker
   auto-discovers workflows under `src/workflows/`.
- Confirm the structure loads: `python verify.py --selftest`.

---

## Tasks (easy to hard)

### Task 1 - Get the skeleton loading

- **Objective:** confirm the starter is discoverable before changing code.
- **Scenario:** you dropped the files into a scaffold and want a known-good baseline.
- **Hint (evidence, not fix):** run `python verify.py --selftest`. It reports
  whether the module loads and whether all three handler names are found.
- **Acceptance:** selftest prints all three handlers discoverable and exits 0.

### Task 2 - Fix the query so it stops mutating state

- **Objective:** make `get_status` a true read.
- **Scenario:** the dashboard polls `get_status` constantly. Right now every
  poll changes the case, so the numbers drift on their own.
- **Hint (evidence, not fix):** read `get_status` in `triage_workflow.py`. It
  carries the marker `# TODO: this query mutates state`. A query handler is
  non-async and must be side-effect-free. Ask: what line here changes state on
  a read?
- **Acceptance:** `get_status` performs no assignment to `self.*`; it only reads
  and returns.

### Task 3 - Make a signal actually wake the workflow

- **Objective:** replace the busy-loop with `wait_condition`.
- **Scenario:** notifications are being delivered, but a status query taken right
  after a signal shows nothing new. The case history is invisible.
- **Hint (evidence, not fix):** the entrypoint carries the marker
  `# TODO: notifications never wake the workflow`. The loop spins without ever
  suspending on a change. `wait_condition(lambda: ...)` suspends the workflow
  until the predicate is true, so a signal wakes it durably instead of the loop
  burning cycles past the change. Do not clear the notifications; advance a
  cursor so the query keeps reflecting the full history.
- **Acceptance:** after a signal, a follow-up `get_status` reports
  `notification_count >= 1`.

### Task 4 - Implement the update so it returns a confirmation

- **Objective:** turn the `set_priority` stub into a working update.
- **Scenario:** an agent raises the case to priority 4 and needs to know it took.
- **Hint (evidence, not fix):** `set_priority` currently raises
  `NotImplementedError`. An update may mutate state and may await an activity,
  and it returns a value. The caller needs a confirmed result, which is exactly
  why this is an update and not a signal (a signal returns nothing).
- **Acceptance:** the update returns a dict reporting the new priority, and a
  follow-up query shows that priority.

### Task 5 - Run it end to end

- **Objective:** drive all three primitives against a live execution.
- **Scenario:** you prove state reflects every interaction.
- **Steps:**
  - In one terminal: `make start-worker`.
  - In another terminal: `python verify.py`.
  - The harness triggers the workflow with `make`-style execution, sends a
     signal, queries, updates, and queries again.
- **Hint (evidence, not fix):** if the query returns stale state after the
  signal, that is Task 3 not finished, not a signal problem. Trace it from the
  query showing stale state, not from the log.
- **Acceptance:** `python verify.py` prints GREEN and exits 0.

---

## Best practices and pitfalls

- **Match the primitive to the need.** Signal for fire-and-forget, query for
  read-only state, update when the caller needs a confirmed result.
- **Never mutate state in a query handler.** Queries must be side-effect-free.
  They are not durably logged the way signals and updates are, so a mutation in
  a query is both wrong and untraceable.
- **Declare handler parameters explicitly.** The declared params are the payload
  contract; the SDK rejects extra or mistyped fields with HTTP 422. That
  validation is a feature, not a nuisance.
- **Use `wait_condition`, not a polling loop.** A signal-driven workflow that
  busy-loops stays expensive and can miss the change it is spinning on. The
  common failure is a workflow that never reacts to a signal because it did not
  `wait_condition` on the change. You will see it as a query showing stale
  state, not as an error in the log.

## Stretch

- Add validation to the update: reject an out-of-range priority. The solution
raises when the priority is outside `[1, 5]`. Send `{"priority": 99}` and
confirm the request is refused and a follow-up query shows the priority
**unchanged**.

- Then reason about it: why is an update, not a signal, the right place to enforce
this? A signal returns nothing, so the caller would never learn the request was
rejected, and bad state could slip in silently. The update rejects before it
mutates and tells the caller why. This is also where the payload contract earns
its keep: a mistyped field is rejected with HTTP 422 before your handler even
runs.

---

## What you learned

- The three interaction primitives and the single question that picks between
  them: does the caller need a return value, and does the call change state?
- Why `wait_condition` is what makes a signal-driven workflow durable and cheap.
- Why validation belongs in an update, and how the payload contract backs it up.

- **Next:** A4 continues the workshop. See the WFLOW-WS1 activity index.
