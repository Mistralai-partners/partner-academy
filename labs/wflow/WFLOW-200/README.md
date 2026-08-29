<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Intermediate (WFLOW-200)

# WFLOW-200 Lab - Mistral Workflows Intermediate (L200)

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, the two-terminal worker setup, and a troubleshooting table.

Working reference code for **Mistral Workflows Intermediate (WFLOW-200)**, the
L200 (Apply) tier. Five production-ready pipeline modules: define a workflow and
activity, configure timeout/retries/heartbeat, use signals/queries/updates, wire
a durable agent, and offload large payloads. This is **working code you read and
run**, not a broken starter you repair.

Read the pipeline modules before you run anything:

- `app/pipeline/hello.py` - define a workflow + activity (`HelloWorkflow` + `greet`).
- `app/pipeline/activity_config.py` - configure timeout, retries, heartbeat.
- `app/pipeline/interactions.py` - signal, query, update on a running workflow.
- `app/pipeline/agent.py` - wire a simple durable agent.
- `app/pipeline/payload.py` - offloadable field for large payloads.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/wflow/WFLOW-200/app
```

Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
# 1. Read the pipeline modules (start with hello.py), then confirm:
python3 verify.py                        # RESULT: PASS
```

`verify.py` runs structural acceptance checks using the REAL `mistralai-workflows`
SDK (registration, introspection, activity metadata) plus live logic for pure
functions. No network calls, no API key needed. A green result never depends on a
live model call.

## Notes

- No API key needed. `uv` fetches `mistralai-workflows` automatically.
- The checks use real SDK registration and introspection (not mocks).
