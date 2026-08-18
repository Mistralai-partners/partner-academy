# MAIS-400 Lab - Mistral AI Studio Expert (hands-on)

**Tier:** L400 (Expert - Evaluate/Create). **Behavior this lab grades:** make and
*defend* an expert design decision on a production AI Studio system under competing
latency, cost, quality, and safety constraints - then prove the decision with a
runnable check. Each task names its Bloom level; the point is not just to make the
check pass but to be able to say *why* your choice beats the plausible alternative.

**Prereqs:** [uv](https://docs.astral.sh/uv/) installed, a Mistral API key.
Copy `.env.example` to `.env` and set `MISTRAL_API_KEY` (or export it).
Work in `starter/`. Reference solutions are in `solution/`.

**Run one task** (pinned SDK):
```
uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python starter/t1_batch_reconcile.py
```
**Run every check:** `bash verify/check.sh starter` - you are done when it
reports **6 passed, 0 failed**. Each script prints `TASKn PASS` and exits 0 on
success; a task fails until you fix its bug.

**How to work it:** each `tN` file has a real bug marked `# BUG` / `# TODO`. Read
the acceptance for the task, decide the design move that satisfies it (and why the
obvious alternative is worse), implement it, then run the check. **Ramp note:**
Task 1 submits a *real* batch job that takes about a minute to finish - start it
early and read the other tasks while it runs.

Every SDK call below is grounded in `platform-docs-public/public/studio-api/`
(pinned) and the `mistralai` Python SDK (context7 `/mistralai/client-python`).

---

## Task 1 - Batch cost optimization + `custom_id` reconciliation (Evaluate)
`starter/t1_batch_reconcile.py`

- **Objective (Evaluate):** judge whether a batch job's SUCCESS status can be
  trusted, and design reconciliation that surfaces silent per-request failures.
- **On the job:** a million-request batch reports SUCCESS - shipping the output
  file as-is would silently drop the rows that failed at inference. You own the
  reconciliation that makes "done" mean "every id accounted for."

A batch job runs at a 50% discount but returns a top-level status that hides
per-request failures. The starter submits four requests (one is malformed at
inference time) and its `reconcile()` trusts `status == SUCCESS` and reads only
the output file. Fix `reconcile()` to account for **every** `custom_id` across
**both** the output file and the error file, and to surface any row whose
`response.status_code` is not 200.
**Acceptance:** the check reports `missing=0` and at least one `failed` id even
though the job status is `SUCCESS`. SDK: `files.upload(purpose="batch")`,
`batch.jobs.create(endpoint="/v1/chat/completions")`, `batch.jobs.get`,
`files.download`.

## Task 2 - Prompt-caching cost analysis + miss diagnosis (Analyze)
`starter/t2_cache_cost.py` - **offline / structural** (see below)

- **Objective (Analyze):** compute the true billable cost of a cached-prefix
  workload and diagnose why a prefix that "should" cache never does.
- **On the job:** finance asks why the caching win is smaller than promised. You
  trace it to a prefix under the 64-token block size and a first-call miss - and
  you can show the billing math that proves it.

Fix the billing math and cache-miss diagnosis to match the documented rules:
billable input = `prompt_tokens - cached_tokens`; cached tokens bill at 10%;
cache blocks are 64 tokens; a prefix under 64 tokens can never hit; a stuck
`cached_tokens == 0` usually means an unstable prefix or a first call.
**Acceptance:** `billable_input_tokens`, `effective_input_cost_ratio`, and
`diagnose` return the documented values for the hit / miss / short fixtures.
**Why offline:** the pinned SDK (`mistralai==1.9.11`) does not expose a
`prompt_cache_key` field, and automatic prefix caching returned
`cached_tokens=None` in this environment, so a live cache hit cannot be produced
deterministically. The expert reasoning is verified against captured/synthetic
usage objects instead.

## Task 3 - Advanced embeddings: retrieval quality (Evaluate)
`starter/t3_embeddings_rerank.py`

- **Objective (Evaluate):** measure retrieval quality with recall@k / MRR and
  choose the grounded re-ranking move over a plausible-but-ungrounded one.
- **On the job:** retrieval "feels off" but nobody has numbers. You put recall@k
  and MRR on it, then re-rank with the embedding similarity you already have -
  and can defend *not* reaching for an ungrounded dedicated re-ranker.

You cannot eyeball retrieval quality - you measure it. The starter ranks
candidates in the wrong order, so recall@k and MRR collapse. Fix `retrieve()` to
rank by cosine similarity, most-relevant first. The grounded expert move is to
re-rank first-stage candidates with the embedding similarity you already have,
not to reach for an ungrounded dedicated re-ranker.
**Acceptance:** `recall@3 >= 0.99` and `MRR >= 0.80` on the labeled query set.
SDK: `embeddings.create(model="mistral-embed", inputs=[...])`.

## Task 4 - Reliable structured output (Apply/Evaluate)
`starter/t4_structured_output.py`

- **Objective (Apply/Evaluate):** design a strict `json_schema` contract that a
  downstream parser can never break on, and judge strict schema vs plain JSON mode.
- **On the job:** an integration crashes whenever the model omits a field or
  returns prose. You harden the boundary with a strict schema so the output is a
  guaranteed shape, not a hope.

A downstream service parses your JSON automatically and must never break on a
missing field. The starter returns prose. Enforce a **strict** `json_schema`
(`additionalProperties=false`, all fields required, `strict=true`) so the output
always parses with `sku`, `quantity`, `unit_price` and the right types.
**Acceptance:** the output parses as JSON with all required keys and correct
types. SDK: `chat.complete(response_format={"type":"json_schema", ...})`.

## Task 5 - Resilient function-result error loops (Apply)
`starter/t5_tool_error_loop.py`

- **Objective (Apply):** keep a tool loop resilient by returning a structured
  error result into the conversation instead of raising.
- **On the job:** one missing lookup should not take down the whole assistant.
  You feed the failure back to the model as a tool result so it recovers and
  still produces a final answer.

In a tool loop a lookup misses. The starter raises, which crashes the
integration. Make `get_inventory` return a **structured error result** back into
the conversation so the model recovers and produces a final answer.
**Acceptance:** the loop finishes with `finish_reason == "stop"` and a non-empty
answer, no exception. SDK: `chat.complete(tools=..., tool_choice=...)` + a
`{"role":"tool", ...,"tool_call_id":...}` message.

## Task 6 - Defense-in-depth: moderate the output path (Evaluate/Create)
`starter/t6_moderation_defense.py`

- **Objective (Evaluate/Create):** design a defense-in-depth safety posture -
  reason about where an unsafe string can enter, and add moderation on the path
  the input guardrail cannot see.
- **On the job:** the user's prompt is clean, but a tool result injects unsafe
  content on the way out. You place a Moderation check on the output/tool-result
  path so nothing unsafe reaches the user, and can justify why input-only
  moderation was insufficient.

Input guardrails alone are not enough: an unsafe string enters through a tool
result while the user's own input is benign. Add a Moderation check on the
output / tool-result path so the unsafe content is caught before delivery.
**Acceptance:** the pipeline blocks with `reason == "output"`. SDK:
`classifiers.moderate(model="mistral-moderation-latest", inputs=[...])`.

---

## When you are done

`bash verify/check.sh starter` reports **6 passed, 0 failed**. You have made six
expert calls under real constraints - batch reconciliation, caching economics,
measured retrieval quality, a strict output contract, a resilient tool loop, and
a defense-in-depth safety posture - and proved each with a runnable check. The
expert bar is being able to defend each choice over its alternative; if you can,
you are ready. **Next:** carry these into a design review - given a production
scenario, choose and justify the posture across all six levers at once.

**Cost note:** every task uses small models (`mistral-small-latest`,
`ministral-3b-latest`, `mistral-embed`, `mistral-moderation-latest`), tiny
inputs, and low `max_tokens`. Task 1 submits a real batch job that finishes in
about one minute.
