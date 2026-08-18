# WFLOW-400 Lab — Mistral Workflows Expert (hands-on)

**Tier:** L400 (Expert — Evaluate/Create). **Behavior this lab grades:** architect,
optimize, and *defend* production Workflows at the edges — design against hard
platform limits, predict sandbox/replay behavior, and choose the right primitive or
policy under competing constraints. Each task names its Bloom level; the centerpiece
(Task 2) is a Create task where you design one workflow that satisfies four hard
constraints at once. The bar is not just a green check — it is being able to justify
each design move.

**How to work it:** each `pipeline/*.py` module has one deliberate expert-level
defect or gap, marked with a `# BUG` / `# TODO` comment. For each task, read the
*Check* (its acceptance), decide the design that satisfies it, implement it, and
re-run. **Ramp note:** Task 1 (find the non-deterministic calls) is the on-ramp and
sets up the same file Task 2 then rebuilds; Task 2 is the hardest — budget the most
time for it. Tasks 3–6 are independent modules.

Prereqs: Python 3.12+, `uv` installed, network access to PyPI. No Mistral API key is required:
every check runs locally (structural validation via the real SDK, plus live AES-GCM crypto).

Work in `starter/`. Run the checks any time:

```bash
bash verify/check.sh starter    # your progress
bash verify/check.sh solution   # the reference (all pass)
```

You are done when `bash verify/check.sh starter` reports **6 passed, 0 failed**.
Reference solution: `solution/pipeline/`.

## What is and isn't executable here (read this first)

Mistral Workflows runs in **hybrid mode**: Mistral hosts the durable orchestrator (Temporal),
and your **worker** runs your `@workflow.define` / `@activity` code. Actually *running* a workflow
(replay, schedules firing, continue-as-new at runtime) needs the live orchestrator plus a running
worker, which is not available as an offline, deterministic self-check. So this lab verifies
everything that *is* real and checkable without the orchestrator:

- **Structural validation via the real `mistralai-workflows` SDK** — the SDK validates and registers
  your workflow definitions (it rejects bad signatures at decoration time), so `get_workflow_definition`
  and the offloading/encryption/schedule types are genuine, not mocks.
- **Live cryptography** — Task 3 encrypts and decrypts with the exact AES-GCM cipher the SDK uses.
- **Pure logic** — Tasks 4 and 5 compute the retry budget and choose ops policies deterministically.

## Tasks

1. **Make the workflow deterministic (Analyze).** *On the job: a workflow that passes locally
   fails on replay in production because its body is non-deterministic — you make it replay-safe.*
   In `pipeline/processor.py`, the `run` entrypoint
   calls `uuid.uuid4()`, `datetime.now()`, `random.random()`, and reads a file directly — all banned
   in workflow code because they break replay. Replace them with `workflow.uuid4()`, `workflow.now()`,
   `workflow.random()`, and move all I/O into activities.
   *Check:* the determinism linter (mirrors the SDK sandbox's banned list) finds zero violations.

2. **Design the four-constraint workflow (Create — the centerpiece).** *On the job: a customer needs a
   PII-safe document pipeline that runs forever over huge payloads — you design the one architecture
   that satisfies every hard constraint at once.* Rework `pipeline/processor.py`
   into ONE workflow that simultaneously satisfies: (1) payloads > 2MB via activity-field offloading
   (`OffloadableModel` / `OffloadableField`); (2) PII encrypted at rest via `EncryptedStrField`;
   (3) indefinite runtime via `continue_as_new` guarded by `should_continue_as_new()`, with the state
   carried forward as `run` parameters; (4) per-iteration determinism by keeping every side effect in
   granular activities (at least three) and the body pure orchestration.
   *Check:* `PagePayload` subclasses `OffloadableModel`; `customer_ssn` is `EncryptedStrField`; the
   workflow registers with `enforce_determinism=True`; `run` accepts the carry-forward params and calls
   continue-as-new; at least three `@activity` functions exist.

3. **Fix the AES-GCM encryption (Evaluate).** *On the job: a security review flags that encrypted-at-rest
   history is using a fixed nonce — you judge why that breaks AES-GCM and fix it correctly.*
   In `pipeline/codec.py`, `encrypt_payload` reuses a fixed
   nonce for every message — catastrophic for AES-GCM. Generate a fresh 12-byte nonce per call, prepend
   it to the ciphertext, and split it back off on decrypt. Build the cipher from the SDK
   (`PayloadEncoder(...).encryptor_main`).
   *Check (live crypto):* round-trip recovers plaintext; two encryptions of the same plaintext differ;
   a tampered ciphertext fails; a wrong key fails.

4. **Compute the retry backoff budget (Analyze).** *On the job: you must tell an SRE the true worst-case
   latency a failing activity can add — so you model the retry backoff the worker actually uses.*
   In `pipeline/retry_budget.py`, `backoff_delays`
   grows linearly. Make it exponential (base 1s, coefficient 2.0), matching how the worker retries a
   failed activity, so `worst_case_backoff` reflects true worst-case latency.
   *Check:* `backoff_delays(5) == [1, 2, 4, 8]` and `worst_case_backoff(5) == 15.0`.

5. **Choose the right ops policies (Evaluate).** *On the job: a sync job is piling up a backlog and a
   paginated fetch is mis-tuned — you pick the overlap policy and executor that fit each scenario.*
   In `pipeline/ops_plan.py`: (a) the sync schedule uses
   `BUFFER_ALL`, which builds an unbounded backlog — switch to `SKIP` (only the latest run matters);
   (b) `choose_executor` always returns offset pagination — return the **List** executor for a fully
   materialized collection and the **Chain** executor for a continuation-token stream.
   *Check:* schedule overlap is `SKIP`; executor selection matches the scenario.

6. **Pick child workflow vs activity (Analyze).** *On the job: a long-running enrichment step needs its
   own durability and retry lifecycle — you decide it should be a child workflow, not an activity.*
   In `pipeline/orchestrator.py`, the long-running,
   independently-durable `enrich_record` is modeled as an activity. Promote it to a child workflow
   (`@workflows.workflow.define(name="enrich-record")`) invoked from the parent via
   `workflows.execute_workflow(...)`, handling a child `WorkflowError`. Keep `notify` an activity.
   *Check:* `EnrichRecord` registers as a workflow and the parent calls `execute_workflow`.

## When you are done

`bash verify/check.sh starter` reports **6 passed, 0 failed**. You have designed
and defended six edge-of-the-platform decisions — determinism, a four-constraint
production architecture, correct AES-GCM, the true retry budget, the right ops
policies, and child-workflow-vs-activity. That design-and-justify skill is the
Expert bar. If you can explain *why* each choice beats its alternative, you are
ready to review other teams' Workflows designs.

All APIs are grounded in the pinned `mistralai/platform-docs-public` Workflows docs
(`public/studio-api/workflows/`).
