<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Expert (WFLOW-400)

# WFLOW-400 Lab — Mistral Workflows Expert (L400)

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python) and the pinned SDK version. This lab runs offline with one command (`python3 verify.py`); it needs no `MISTRAL_API_KEY` and no separate worker process.

Hands-on lab for **Mistral Workflows Expert (WFLOW-400)**. Sixteen tasks — one per course lesson —
exercising the edge-of-the-platform skills the course grades: the execution mental model and the
history cap, determinism enforcement, activity configuration and flavors, the three interaction
primitives, child workflows and typed errors, durable agents with safe MCP credentials, connectors
with on-behalf-of OAuth, publishing and consuming streaming events, conversational workflows for
Vibe, concurrency executors, payload offloading + encryption + key rotation, scheduling, deployment
management, and observability.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/wflow/WFLOW-400/app
```

## What's in the box

- `pipeline/` — one runnable module per lesson (`mental_model`, `determinism`, `activity_config`,
  `flavors`, `interactions`, `orchestrator`, `agent`, `connectors`, `streaming`, `consume`,
  `conversational`, `concurrency`, `processor` + `codec`, `scheduling`, `deployment`,
  `observability`), plus `retry_budget` and `ops_plan` reused for the budget/executor math and a
  `determinism_antipattern` fixture the linter flags.
- `checks.py` — deterministic acceptance checks for all sixteen tasks (real SDK + live AES-GCM).
- `detlint.py` — AST determinism linter mirroring the SDK sandbox's banned-call list.
- `verify.py` — one-command runner: fetches the pinned SDK via `uv` and delegates to `checks.py`.

## The Workflows model (one paragraph)

You write workflows in Python with the `mistralai-workflows` SDK; durable execution is powered by
Temporal in **hybrid mode** — Mistral hosts the orchestrator, your **worker** runs your
`@workflow.define` / `@activity` code. Workflow bodies must be **deterministic** (replayed from an
event history); all side effects live in **activities**. Expert concerns: the 2MB payload limit
(offloading), SDK-layer AES-GCM encryption and key rotation, the ~51,200-event history cap
(continue-as-new), retry backoff, concurrency executors, schedule overlap policy, durable agents,
connectors with on-behalf-of, streaming events, conversational workflows, deployment routing, and
observability traces.

## Executable boundary (honest)

Running a workflow end to end needs the live orchestrator plus a running worker, which is not an
offline, deterministic self-check. This lab verifies what is genuinely real without the
orchestrator, and each check's message says which mode it used: **live logic** (history-cap math,
retry budget, resume arithmetic, routing/poller/reset-point logic, error classification), **live
crypto** (AES-GCM round-trip + key rotation), and **structural validation through the real SDK**
(registration and introspection). The genuinely platform-only behaviours — the agent loop and live
MCP call, live OAuth/OBO, live SSE consume, live Vibe render, live schedule create/pause/resume,
live reset/routing, live trace fetches — are each checked structurally via real SDK objects plus an
offline pure-logic sibling, and labeled in every module's docstring. No check fakes a pass.

## Run

```bash
python3 verify.py          # 16 passed, 0 failed
```

No Mistral API key needed. `uv` fetches `mistralai-workflows[mistralai]==3.10.0` automatically.
Done when `python3 verify.py` reports **16 passed, 0 failed**.
