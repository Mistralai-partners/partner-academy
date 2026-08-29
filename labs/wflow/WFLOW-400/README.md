<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Expert (WFLOW-400)

# WFLOW-400 Lab — Mistral Workflows Expert (L400)

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

Hands-on lab for **Mistral Workflows Expert (WFLOW-400)**. Six expert tasks exercising the
edge-of-the-platform skills the course grades: determinism enforcement, a four-constraint
production design (payload offloading + encryption + continue-as-new + activity-bound design),
AES-GCM payload encryption, the activity retry budget, concurrency/scheduling policy choice, and
child-workflow-vs-activity design.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/wflow/WFLOW-400/app
```

## What's in the box

- `pipeline/` — six solution modules, one per task.
- `checks.py` — deterministic acceptance checks for all six tasks (real SDK + live AES-GCM).
- `detlint.py` — AST determinism linter mirroring the SDK sandbox's banned-call list.
- `verify.py` — one-command runner: fetches the pinned SDK via `uv` and delegates to `checks.py`.

## The Workflows model (one paragraph)

You write workflows in Python with the `mistralai-workflows` SDK; durable execution is powered by
Temporal in **hybrid mode** — Mistral hosts the orchestrator, your **worker** runs your
`@workflow.define` / `@activity` code. Workflow bodies must be **deterministic** (replayed from an
event history); all side effects live in **activities**. Expert concerns: the 2MB payload limit
(offloading), SDK-layer AES-GCM encryption, the ~51,200-event history cap (continue-as-new), retry
backoff, concurrency executors, and schedule overlap policy.

## Executable boundary (honest)

Running a workflow end to end needs the live orchestrator plus a running worker, which is not an
offline, deterministic self-check. This lab therefore verifies what is genuinely real without the
orchestrator: **structural validation through the real SDK** (it registers and validates your
definitions), **live AES-GCM crypto** (Task 3), and **pure logic** (Tasks 4-5). See `tasks.md` for
the full explanation.

## Run

```bash
python3 verify.py          # 6 passed, 0 failed
```

No Mistral API key needed. `uv` fetches `mistralai-workflows[mistralai]==3.10.0` automatically.
Done when `python3 verify.py` reports **6 passed, 0 failed**.
