# WFLOW-300 Lab — Mistral Workflows Advanced (hands-on)

**Tier:** L300 (Advanced — Analyze). **Behavior this lab grades:** handle the hard cases —
reason about correctness under failure, root-cause non-obvious production failures, and choose
the right mechanism under competing constraints. Every task is a **diagnose-and-fix** on a
workflow that looks fine until it meets retries, replay, scale, or multiple users. The bar is
not just a green check; it is being able to explain *why* the failure happened and why the fix
removes it.

**How to work it:** each `pipeline/*.py` module reproduces one production symptom, marked with a
`# SYMPTOM` comment that names what goes wrong, never the fix. For each task, read the *Hint*
(where the evidence is), diagnose the cause, implement the fix, and re-run. Tasks are
independent; work them in any order. Task 5 is the gentlest on-ramp (pure logic, no SDK).

Prereqs: Python 3.12+, `uv` installed, network access to PyPI. No Mistral API key is required.

```bash
bash verify/check.sh starter    # your progress
bash verify/check.sh solution   # the reference (all pass)
```

You are done when `bash verify/check.sh starter` reports **6 passed, 0 failed**.
Reference solution: `solution/pipeline/`.

## What is and isn't executable here (read this first)

Mistral Workflows runs in **hybrid mode**: Mistral hosts the durable orchestrator (Temporal) and
your **worker** runs your `@workflow.define` / `@activity` code. Actually *running* a workflow
(replay after a restart, real signal suspension, live OBO routing) needs the orchestrator plus a
running worker, which is not an offline, deterministic self-check. This lab therefore verifies
everything that *is* real without the orchestrator, and labels each check:

- **Live logic (fully offline).** Task 4 selects executors and Task 5 models the
  `broker_sequence` resume guarantee — both run real code and real SDK objects. Task 1 runs the
  charge activity twice to reproduce a double-charge live.
- **Structural via the real SDK.** Tasks 2, 3, and 6 register and introspect your definitions
  through the actual `mistralai-workflows` SDK (it rejects bad signatures and enforces the
  `on_behalf_of` constraints at decoration time), so signals, determinism flags, and OBO are
  genuine, not mocked.
- **AST determinism linter.** Task 3 also runs `verify/detlint.py`, which mirrors the sandbox's
  banned-call list from `workflows/determinism.md`.

What stays **structural-only** (and why): real replay non-determinism (Task 3 checks the contract
the sandbox enforces, not an actual restart), real signal-driven suspension (Task 2), and the
hardened-deployment requirement + live per-user routing for OBO (Task 6 — hardening is a console
setting and routing needs the orchestrator). These are called out honestly; nothing fakes a pass.

## Tasks

### 1. Idempotency under retry (Analyze)
- **Objective:** *Analyze* why a retried activity double-charges and make the retry idempotent.
- **Scenario:** A charge activity occasionally times out mid-run and is retried, sometimes
  billing the customer twice. On the job this is a Sev-1.
- **Hint:** The platform retries an activity with the *same inputs*. Look at where the "have I
  already charged this?" key comes from, and whether it is stable across attempts. A key minted
  *inside* the activity is new on every retry.
- **Acceptance:** Calling the charge activity twice with identical inputs records **one** charge
  (live), and the workflow derives the key with `workflow.uuid4()` and passes it to the activity
  (so the fix is not a degenerate dedupe on `customer_id`).

### 2. wait_condition + signal + timeout, together (Analyze)
- **Objective:** *Analyze* which primitive each of three symptoms needs and combine them.
- **Scenario:** A human-in-the-loop approval pins a CPU, drops the approvals sent to it, and
  hangs forever when no one approves.
- **Hint:** Three separate defects. One is about *how it waits*, one about *how the outside
  reaches it*, one about *what happens when nobody acts*. See `signals.md` and
  `waiting_for_conditions.md`.
- **Acceptance:** an `approve` signal is registered (SDK), and `run` suspends on
  `workflow.wait_condition(..., timeout=...)` and handles `asyncio.TimeoutError`, with no
  busy-wait loop.

### 3. Post-restart non-determinism (Analyze)
- **Objective:** *Analyze* which values break replay and relocate them.
- **Scenario:** A workflow passes every local run, then fails with a non-determinism error in
  production after a worker restart.
- **Hint:** The body is re-executed from event history on replay. Which values would differ
  between the first run and the replay? Which lines do I/O that must not be replayed? Deterministic
  APIs live under `workflow.*`; side effects belong in an `@activity`. The escape hatches
  (`workflow.unsafe.imports_passed_through()`, `workflow.unsafe.skip_determinism_enforcement()`)
  exist for import-time side effects and one-off safe reads — they are a last resort, not the fix
  here.
- **Acceptance:** the determinism linter finds zero violations in the workflow body and the
  workflow still registers with `enforce_determinism=True`.

### 4. The right concurrency executor at scale (Analyze)
- **Objective:** *Analyze* how each source is addressable and choose the matching executor + knobs.
- **Scenario:** 500,000 records fetched page-by-page, a stream that only hands back a continuation
  token, and a collection already in memory — all currently forced through offset pagination.
- **Hint:** The choice depends on *how you can address the next item*, not on item count. One
  source is index-addressable, one is token-chained, one is materialized. Note which concurrency
  knob is offset-only (`concurrency.md` parameter matrix).
- **Acceptance:** offset for the 500k index-addressable case (with `n_items` and
  `max_concurrent_executions_per_worker`, and a real `@activity` for `get_item_from_index_activity`),
  chain for the token stream (no concurrency knobs), list for the materialized collection (no
  offset-only knob). Runs live.

### 5. Resilient stream resume (Analyze)
- **Objective:** *Analyze* the `broker_sequence` guarantee and resume without gaps or duplicates.
- **Scenario:** After a mid-stream disconnect, the consumer re-delivers an event and reconnects
  back-to-back with no growing delay.
- **Hint:** `broker_sequence` is ordered, unique, and resume-safe: reconnecting with `start_seq=N`
  picks up *exactly* from N. Where should the stream resume relative to the last sequence you saw,
  and how should the reconnect delay grow? `consume_stream` is fixed — fix the two decision
  functions. See `streaming.md` ("Sequence Guarantee"). This task is pure logic and runs live.
- **Acceptance:** `next_start_seq(41) == 42`; the six-event stream is delivered exactly once in
  order across the forced reconnect; `reconnect_backoff` grows until it is capped.

### 6. Per-user Connector access via on-behalf-of (Apply)
- **Objective:** *Apply* the OBO setting so a shared workflow resolves each user's own connectors.
- **Scenario:** A per-user PR report shows every user the worker's GitHub data instead of their own.
- **Hint:** A workflow resolves Connector credentials from the identity it runs under. Which
  identity is that by default, and what one setting makes it the triggering user? See
  `on_behalf_of.md` and `connectors.md`. For the write-up: OBO **requires** a hardened deployment
  and **cannot** be combined with `schedules` — both are enforced beyond this file.
- **Acceptance:** the workflow registers with `on_behalf_of=True` and no schedule conflict (SDK).
  The hardened-deployment requirement is structural-only here (a console setting); note it in your
  runbook.

## When you are done

`bash verify/check.sh starter` reports **6 passed, 0 failed**. You have diagnosed and fixed six
production-shaped failures — a double-charge under retry, a broken approval, a replay-only
non-determinism, a mis-chosen executor, a duplicating stream resume, and a cross-user identity
leak. If you can explain the root cause of each in one sentence, you are ready for WFLOW-400
(Expert), where you design and defend these decisions from scratch.

All APIs are grounded in the pinned `mistralai/platform-docs-public` Workflows docs
(`public/studio-api/workflows/`, SHA `a3e0f0c…`).
