# WFLOW-200 Lab — Mistral Workflows Intermediate (hands-on)

**Tier:** L200 (Intermediate — Apply). **Behavior this lab grades:** do the real day-to-day
work of building a workflow. You **build** the everyday pieces from a starter that only sketches
them: a workflow plus its activity, correct activity configuration, the three ways the outside
world interacts with a running workflow, a simple durable agent, and payloads that stay under the
2MB limit. The bar is not memorizing names — it is wiring each piece so it actually runs and
registers.

**How to work it:** each `pipeline/*.py` module has `TODO(Tn)` markers that name what to build
(never the finished code). For each task, read the *Hint* (where the pattern lives in the docs),
build the piece, and re-run. Tasks are independent; work them in any order. Task 1 is the on-ramp.

Prereqs: Python 3.12+, `uv` installed, network access to PyPI. No Mistral API key is required.

```bash
bash verify/check.sh starter    # your progress
bash verify/check.sh solution   # the reference (all pass)
```

You are done when `bash verify/check.sh starter` reports **5 passed, 0 failed**.
Reference solution: `solution/pipeline/`.

## What is and isn't executable here (read this first)

Mistral Workflows runs in **hybrid mode**: Mistral hosts the durable orchestrator (Temporal) and
your **worker** runs your `@workflow.define` / `@activity` code. Actually *running* a workflow
end to end (or a live agent turn) needs the orchestrator plus a running worker, which is not an
offline, deterministic self-check. This lab verifies everything that *is* real without the
orchestrator, and labels each check:

- **Live logic (fully offline).** T1, T2, T3, and T5 execute your real activities and Pydantic
  models — greeting output, activity return values, the deterministic price, and the offloadable
  payload round-trip all run live.
- **Structural via the real SDK.** Every task registers your workflow through the actual
  `mistralai-workflows` SDK (`get_workflow_definition`), so workflow names, and the signal /
  query / update handlers, are genuine, not mocked. T2 reads the activity's real
  `__wf_activity_params__` metadata (the timeout / retry / heartbeat the SDK recorded). T4 builds
  the `Agent` and `RemoteSession` objects offline and introspects them.

What stays **structural-only** (and why): the agent turn in T4 — `Runner.run(...)` needs the live
Mistral Agents API, so it is not executed here; the check confirms the agent is wired correctly
(tool, model, session) and the workflow registers. This is called out honestly; nothing fakes a
pass.

## Tasks

### 1. Define a workflow and its activity (Apply)
- **Objective:** *Apply* the core scaffold — one workflow whose entrypoint runs one activity.
- **Scenario:** Every workflow you ship starts here: deterministic orchestration in the body, real
  work in an activity. Getting this shape right is the foundation for everything else.
- **Hint:** The activity does the work and returns the greeting; the entrypoint only calls it. See
  `your_first_workflow.md` for the exact decorators (`@workflows.activity()`,
  `@workflows.workflow.define(name=...)`, `@workflows.workflow.entrypoint`).
- **Acceptance:** `greet` runs live and returns a greeting containing the name; `HelloWorkflow`
  registers as `hello-world`; the entrypoint calls the activity rather than building the string
  inline.

### 2. Configure an activity's timeout, retries, and heartbeat (Apply)
- **Objective:** *Apply* the three reliability settings to an activity that calls a flaky API.
- **Scenario:** A bare activity blocks on the default timeout, never retries a transient failure,
  and cannot report a stall. On the job those defaults cause silent hangs and avoidable pages.
- **Hint:** Three separate decorator arguments — one caps a single attempt, one pair drives
  automatic retry with exponential backoff, one detects an unresponsive long call. The exact
  argument names are in `activities/basics.md` (Timeouts / Retry policies / Heartbeat).
- **Acceptance:** the activity's recorded params show `retry_policy_max_attempts >= 2`, a backoff
  coefficient, and a heartbeat timeout; an explicit `start_to_close_timeout` is set; the activity
  runs live and the workflow registers as `quote-workflow`.

### 3. Interact with a running workflow: signal, query, update (Apply)
- **Objective:** *Apply* the right interaction primitive for each of three needs.
- **Scenario:** An order workflow must be cancellable from the outside, must expose its current
  status, and must let a caller add an item and get the new total back in one call.
- **Hint:** Three different needs map to three different primitives. One is asynchronous and
  returns nothing; one is read-only and returns state; one mutates state, returns a value, and may
  run an activity. The comparison table at the bottom of `signals.md` / `queries.md` / `updates.md`
  is the decision aid — match each need to a row.
- **Acceptance:** a `cancel_order` signal, a `get_status` query, and an `add_item` update are all
  registered (real SDK), the update runs the `price_item` activity, and the activity runs live.

### 4. Wire a simple durable agent (Apply)
- **Objective:** *Apply* the durable-agent wiring inside a workflow.
- **Scenario:** A support workflow answers order questions with an LLM that can call a lookup tool.
  Because the loop runs inside a workflow, its state survives a worker restart — but only if it is
  wired correctly.
- **Hint:** Four parts — an `@activity` used as a tool, an `Agent` that names a model and its
  tools, a session, and `Runner.run`. One session type silently drops built-in tools; the docs say
  which one to prefer for anything production-facing. See `durable_agents.md`.
- **Acceptance:** the agent carries the `lookup_order_status` activity as a tool and a model, the
  session is a `RemoteSession`, the entrypoint drives it with `Runner.run`, and the workflow
  registers as `support-agent-workflow`. (The live agent turn is structural-only — it needs the
  Agents API — so it is not executed here.)

### 5. Payload basics: pass large data by reference (Apply)
- **Objective:** *Apply* activity-field offloading so a >2MB value never lands on the orchestrator.
- **Scenario:** A transcript can exceed the 2MB payload limit. Put the bytes on the orchestration
  layer and the workflow fails; pass a reference and it scales.
- **Hint:** Two rules. The large field belongs to a model that subclasses `OffloadableModel` and is
  typed as an `OffloadableField`. And `.get_value()` is safe only *inside* an activity — in the
  workflow body the value may not be local, so pass the field through untouched. See
  `payload_offloading.md` (Activity field offloading; "Using in workflows").
- **Acceptance:** `TranscriptionPayload` subclasses `OffloadableModel` and its `transcript` is an
  `OffloadableField`; the offloadable payload round-trips live; the workflow body does not call
  `.get_value()`; the workflow registers as `transcribe-workflow`.

## When you are done

`bash verify/check.sh starter` reports **5 passed, 0 failed**. You have built the everyday
Workflows toolkit — a workflow and its activity, a correctly configured activity, the signal /
query / update interaction primitives, a durable agent, and offloadable payloads. If you can say
in one sentence why each piece is shaped the way it is, you are ready for WFLOW-300 (Advanced),
where you diagnose and fix these same primitives under retries, replay, scale, and multiple users.

All APIs are grounded in the pinned `mistralai/platform-docs-public` Workflows docs
(`public/studio-api/workflows/`, SHA `a3e0f0c…`).
