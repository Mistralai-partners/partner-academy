<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Intermediate (WFLOW-200)

# WFLOW-200 Lab — Mistral Workflows Intermediate (L200)

Hands-on lab for **Mistral Workflows Intermediate (WFLOW-200)**. Five **build** tasks exercising
the Apply skills the course grades: define a workflow and its activity, configure an activity's
timeout / retries / heartbeat, interact with a running workflow through signals / queries /
updates, wire a simple durable agent, and keep large payloads under the 2MB limit with activity
field offloading.

- `starter/pipeline/` — begin here. Each module sketches one piece with `TODO(Tn)` markers.
- `solution/pipeline/` — reference solution (all checks pass).
- `verify/check.sh <starter|solution>` — deterministic acceptance checks for all five tasks.
- `tasks.md` — the five tasks, each with objective, scenario, hint, and acceptance.
- `FACILITATOR.md` — instructor-led delivery (agenda, demos, discussion, pitfalls).

## The Workflows model (one paragraph)

You write workflows in Python with the `mistralai-workflows` SDK; durable execution runs in
**hybrid mode** — Mistral hosts the orchestrator (Temporal), your **worker** runs your
`@workflow.define` / `@activity` code. Workflow bodies are deterministic orchestration; all side
effects and real work live in **activities**, which are the retry boundary. External systems
interact with a running workflow through **signals** (async, one-way), **queries** (sync, read),
and **updates** (sync write that can run an activity). A **durable agent** runs the LLM loop inside
a workflow so its state survives restarts. Values larger than the platform's **2MB payload limit**
are passed by reference via **activity field offloading**.

## Executable boundary (honest)

Running a workflow end to end, or a live agent turn, needs the live orchestrator plus a running
worker (and, for the agent, the Mistral Agents API) — not an offline, deterministic self-check.
This lab verifies what is genuinely real without the orchestrator, and each check says which mode
it used: **live logic** (Tasks 1, 2, 3, 5 execute your real activities and Pydantic models),
**structural validation through the real SDK** (every task registers and introspects your
definitions; Task 2 reads the SDK's own `__wf_activity_params__` metadata; Task 4 builds and
introspects the real `Agent` / `RemoteSession`). The only structural-only boundary is the agent
turn in Task 4 (`Runner.run` needs the live Agents API) — it is labeled in `tasks.md`. No check
fakes a pass.

## Run

```bash
bash verify/check.sh solution   # 5 passed, 0 failed
bash verify/check.sh starter    # 5 failed until you complete the tasks
```

No Mistral API key needed. `uv` fetches `mistralai-workflows[mistralai]==3.10.0` automatically.
Done when `bash verify/check.sh starter` reports **5 passed, 0 failed**.
