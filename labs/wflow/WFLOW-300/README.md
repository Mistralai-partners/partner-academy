<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Advanced (WFLOW-300)

# WFLOW-300 Lab — Mistral Workflows Advanced (L300)

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

Hands-on lab for **Mistral Workflows Advanced (WFLOW-300)**. Six advanced **diagnose-and-fix**
tasks exercising the Analyze skills the course grades: idempotency under retry, a combined
`wait_condition` + signal + timeout, post-restart non-determinism, the right concurrency executor
at scale, resilient stream resume via `broker_sequence`, and per-user Connector access with
on-behalf-of.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/wflow/WFLOW-300/app
```

## What's in the box

- `pipeline/` — six solution modules, one per task.
- `checks.py` — deterministic acceptance checks for all six tasks (real SDK introspection + live logic).
- `detlint.py` — AST determinism linter mirroring the SDK sandbox's banned-call list.
- `verify.py` — one-command runner: fetches the pinned SDK via `uv` and delegates to `checks.py`.
- `FACILITATOR.md` (lab root) — instructor-led delivery (agenda, demos, discussion, pitfalls).

## The Workflows model (one paragraph)

You write workflows in Python with the `mistralai-workflows` SDK; durable execution runs in
**hybrid mode** — Mistral hosts the orchestrator (Temporal), your **worker** runs your
`@workflow.define` / `@activity` code. Workflow bodies must be **deterministic** (replayed from an
event history), so all side effects and non-deterministic values live in **activities** or come
from `workflow.*` APIs. Activities are the retry boundary; external systems interact with a running
workflow through **signals** (async), **queries** (read), and **updates** (sync write). At scale you
use the concurrency executors and streaming events, and multi-user workflows resolve credentials
through **on-behalf-of** identity on **hardened deployments**.

## Executable boundary (honest)

Running a workflow end to end (replay after a restart, live signal suspension, OBO routing) needs
the live orchestrator plus a running worker, which is not an offline, deterministic self-check. This
lab verifies what is genuinely real without the orchestrator, and each check says which mode it used:
**live logic** (Tasks 4, 5, and the double-charge reproduction in Task 1), **structural validation
through the real SDK** (Tasks 2, 3, 6 — registration and introspection), and an **AST determinism
linter** (Task 3). Structural-only boundaries (real replay, real suspension, hardened-deployment
setting) are labeled in `tasks.md`. No check fakes a pass.

## Run

```bash
python3 verify.py          # 6 passed, 0 failed
```

No Mistral API key needed. `uv` fetches `mistralai-workflows[mistralai]==3.10.0` automatically.
Done when `python3 verify.py` reports **6 passed, 0 failed**.
