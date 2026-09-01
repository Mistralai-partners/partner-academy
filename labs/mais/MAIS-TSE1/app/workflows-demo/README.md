# WFLOW-TSE1 Lab - Mistral Workflows Tech Sales Essentials

A real, dual-modality lab for the technical seller. It has two halves that map to the TSE job:

1. **Run the demo.** Stand up a small durable workflow (an invoice pipeline) that shows the value
   story a customer asks about: durable orchestration, the activity retry boundary, deterministic
   replay, live progress, and a human approval step.
2. **Scope the fit.** Map a prospect's requirements to the right Workflows primitives, then give the
   honest architecture answer on the on-behalf-of and hardened-deployment constraints.

It replaces a click-through walkthrough with four checkable tasks: two build the demo (verified
through the real `mistralai-workflows` SDK) and two are decision tasks (run live against a fixed
rubric).

- `starter/demo/` - begin here. `invoice_workflow.py` (T1, T2), `scoping.py` (T3),
  `feasibility.py` (T4), each with a `# TODO`.
- `solution/demo/` - the reference (all four checks pass).
- `verify/check.sh <starter|solution>` - runs all four checks; exit code = number of failures.
- `tasks.md` - the four tasks with objective, scenario, hint, and acceptance.
- `FACILITATOR.md` - the instructor-led delivery layer (agenda, talk track, live checkpoints,
  objection handling).

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Run the suite (the pinned SDK is pulled automatically; **no Mistral API key is required**):

```bash
bash verify/check.sh starter     # expect 4 failed until you complete the tasks
bash verify/check.sh solution    # 4 passed, 0 failed
```

Prereqs: Python 3.12+, `uv`, network access to PyPI. The checks pin
`mistralai-workflows[mistralai]==3.10.0`.

## What each task grades

| Task | Behavior | Feature | Check kind |
|---|---|---|---|
| 1 | Build the durable demo | activity boundary, `workflow.uuid4()`, determinism | Structural (real SDK) |
| 2 | Make the demo interactive | `get_status` query + `approve` signal | Structural (real SDK) |
| 3 | Scope the fit | activity / query / signal / offloading / sticky session / encryption | Live logic (offline) |
| 4 | Honest architecture answer | OBO requires hardening; OBO incompatible with schedules | Live logic (offline) |

Done when `bash verify/check.sh starter` reports **4 passed, 0 failed**.

## What is real and what is structural

Workflows runs in **hybrid mode**: Mistral hosts the orchestrator and your worker runs your code. A
real replay after a restart and a live query against a running execution need the hosted
orchestrator plus a running worker, so they cannot be an offline self-check. This lab verifies what
the real SDK confirms offline (registration, activities, queries, signals, determinism flag) and
runs the decision tasks as live logic. Every check message says which kind it is. Nothing is mocked.

All SDK calls and constraints are grounded in the pinned `platform-docs-public`
`public/studio-api/workflows/` docs (SHA `a3e0f0c...`).
