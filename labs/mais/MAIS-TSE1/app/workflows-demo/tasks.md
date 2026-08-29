# WFLOW-TSE1 Lab Tasks - Mistral Workflows Tech Sales Essentials

**Tier:** TSE (Tech Sales Essentials). **Bloom:** Apply-dominant (place the right capability, scope
a fit, give the honest answer) with one Analyze feasibility call.

**Behavior this lab grades:** run a credible Workflows demo for a customer and scope a fit without
over-promising. You will stand up the durable happy-path demo, make it interactive, map a
prospect's requirements to the right primitives, and give honest architecture answers on the OBO
and hardening constraints.

**How to work it:** the demo lives in `demo/`. Tasks 1 and 2 complete the demo workflow and are
verified structurally through the real `mistralai-workflows` SDK. Tasks 3 and 4 are decision tasks
that run as live Python against a fixed rubric. Each task's *Hint* points at the evidence, never the
fix.

```bash
bash verify/check.sh starter    # your progress (starts at 0 passed, 4 failed)
bash verify/check.sh solution   # the reference (4 passed, 0 failed)
```

You are done when `bash verify/check.sh starter` reports **4 passed, 0 failed**.

## What is and isn't executable here (read this first)

Mistral Workflows runs in **hybrid mode**: Mistral hosts the durable orchestrator, and your
**worker** runs your `@workflow.define` / `@activity` code. Actually *running* a workflow (replay
after a restart, a live query against a running execution) needs the orchestrator plus a running
worker, which is not an offline, deterministic self-check.

- **Structural via the real SDK (T1, T2).** Your demo definition is registered and introspected
  through the actual `mistralai-workflows` SDK. The SDK rejects malformed handlers and reports the
  registered activities, queries, signals, and the determinism flag, so what is checked is genuine,
  not mocked. What stays structural-only is a real replay and a live query against a running
  execution; both need the hosted orchestrator and are called out honestly.
- **Live logic, fully offline (T3, T4).** Your scoping map and feasibility decisions run as real
  Python and are checked against a fixed rubric.

Nothing fakes a pass.

## Tasks

### 1. Build the durable demo (Apply)
- **Objective:** *Apply* the workflow-versus-activity split and the deterministic id API so the demo
  actually tells the durability story.
- **Scenario:** You are about to demo an invoice pipeline to a customer. As written, the demo runs
  the PDF fetch inline in the workflow body and mints its id with a raw uuid. A prospect's architect
  will immediately ask "what happens when a worker restarts mid-run?" and this version has no good
  answer.
- **Hint:** The PDF fetch is a side effect (an HTTP download). Side effects are the retry boundary,
  and the workflow body is re-executed from history on replay. Which of the two should hold the
  fetch, and which id source is safe across replay? See `building-workflows/workflows.md`,
  `building-workflows/activities/basics.md`, and `building-workflows/workflows/determinism.md`.
- **Acceptance:** a real `@activity` holds the fetch and the entrypoint awaits it; the body derives
  its id from `workflow.uuid4()` (not the stdlib uuid); and the workflow registers with determinism
  enforcement on (SDK).

### 2. Make the demo interactive (Apply)
- **Objective:** *Apply* queries and signals so the customer can watch and interact during the demo.
- **Scenario:** The strongest moment in a Workflows demo is showing a prospect live progress and a
  human approval step. Your demo currently exposes neither.
- **Hint:** One primitive lets an outside caller *read* running state without changing it; another
  lets a reviewer *nudge* the workflow without waiting for a reply. See
  `interacting-with-workflows/queries.md` and `interacting-with-workflows/signals.md`.
- **Acceptance:** the workflow registers a `get_status` query and an `approve` signal (SDK).

### 3. Scope the fit (Apply)
- **Objective:** *Apply* the Workflows capability vocabulary: place the single right primitive for
  each customer requirement.
- **Scenario:** A prospect lists six concrete needs on a scoping call. Naming the exact primitive
  for each one is what makes you credible instead of hand-wavy.
- **Hint:** Each need maps to exactly one capability. Distinguish "read progress" from "push an
  approval in," and distinguish "data over 2MB stays in the customer's storage" from "the platform
  must never see cleartext" and from "keep a loaded model warm across steps." See
  `payload_offloading.md`, `encryption.md`, and `activities/sticky_worker_sessions.md`.
- **Acceptance:** every entry in `SCOPING` maps to the correct capability key (live).

### 4. Feasibility: the honest architecture answer (Apply / Analyze)
- **Objective:** *Analyze* three asks against the on-behalf-of and hardening constraints and return
  a verdict plus the gating constraint the seller must state out loud.
- **Scenario:** The fastest way to lose a technical evaluation is to promise something the platform
  forbids. Two of these three asks touch OBO, which the platform gates.
- **Hint:** On-behalf-of gives each user their own identity, but it has two hard rules: one about
  the kind of deployment it can register on, and one about a feature it cannot be combined with
  (because that feature has no triggering user). The third ask is a clean fit if the side effect is
  placed correctly. See `building-workflows/on_behalf_of.md` and
  `managing-workflows-in-production/hardened_deployments.md`.
- **Acceptance:** `assess()` returns the correct `verdict` and `constraint` for all three scenarios
  (live).

## When you are done

`bash verify/check.sh starter` reports **4 passed, 0 failed**. You have stood up a durable demo that
survives the architect's hard question, made it interactive, scoped six requirements to the right
primitives, and given honest answers on the OBO and hardening constraints. Next: the practitioner
track (WFLOW-200 onward), where you build and operate these workflows for real.

All APIs are grounded in the pinned `mistralai/platform-docs-public` Workflows docs
(`public/studio-api/workflows/`, SHA `a3e0f0c...`).
