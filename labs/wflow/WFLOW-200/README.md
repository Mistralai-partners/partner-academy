<!-- course-ref -->
**Course:** Mistral AI Studio Workflows: Intermediate (WFLOW-200)

# WFLOW-200 Lab - Mistral Workflows Intermediate (L200)

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python) and the pinned SDK version. This lab needs no
> worker and no `MISTRAL_API_KEY`: you read the modules and run `python3 verify.py`.

Working reference code for **Mistral Workflows Intermediate (WFLOW-200)**, the
L200 (Apply) tier. Twelve production-ready pipeline modules covering the everyday
practitioner skills: define a workflow and activity, configure
timeout/retries/heartbeat, pick an activity flavor, keep a workflow deterministic,
use signals/queries/updates, wire a durable agent, stream and resume events, run
child workflows with continue-as-new and schedules, call a Connector, offload and
encrypt payloads, scale with concurrency and rate limits, and handle production
errors. This is **working code you read and run**, not a broken starter you repair.

Read the pipeline modules before you run anything:

- `app/pipeline/hello.py` - define a workflow + activity (`HelloWorkflow` + `greet`).
- `app/pipeline/activity_config.py` - timeout, retries, heartbeat, and composition.
- `app/pipeline/flavors.py` - regular / local / sticky activity flavors + `Depends`.
- `app/pipeline/determinism.py` - deterministic workflow APIs + the escape hatch.
- `app/pipeline/interactions.py` - signal, query, update on a running workflow.
- `app/pipeline/agent.py` - wire a simple durable agent.
- `app/pipeline/streaming.py` - publish a token stream and resume it without gaps.
- `app/pipeline/child_continue.py` - child workflows, continue-as-new, and schedules.
- `app/pipeline/connectors.py` - call an external service through a Connector slot.
- `app/pipeline/payload.py` - offload large fields and encrypt sensitive ones.
- `app/pipeline/scale.py` - concurrency (gather / parallel executors) + rate limiting.
- `app/pipeline/ops.py` - deployments, observability, and typed structured errors.

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
