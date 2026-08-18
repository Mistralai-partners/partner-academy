# MAIS-300 Lab — Operate, Debug, and Tune a Production AI Studio System

**Tier:** L300 (Advanced — Analyze). **Behavior this lab grades:** *trace a
production failure from its symptom to its root cause and fix it with a small,
correct change.*

You are handed a small `mais/` package a teammate wrote under pressure. Every
module imports and runs, but five behaviors are subtly wrong in ways that only
bite in production — a stream that hangs, a retry storm, a RAG that returns the
wrong passage, a branch off the wrong turn, a storage estimate that blows the
budget. The failing tests are your incident reports. **Your job is to diagnose
each one, not just patch it** — that diagnosis is the Analyze skill the course
grades, so the hints below point you at the evidence and stop short of the fix.

## How to work this lab

- Work in `starter/`. The reference is in `solution/` — use it to check your
  reasoning *after* you have formed your own, not as a first move.
- Run the check any time:
  ```
  bash verify/check.sh starter
  ```
  You are done when it reports **`12 passed`**.
- Each task lives in one file under `starter/mais/`. Every bug is marked with a
  `# BUG (Task N)` comment that names the *symptom*, not the fix — read the
  failing test to work out the cause.
- **Loop for every task:** run the check → read the failing test's assertion
  (what input, what it expects, what the code produces) → form a hypothesis
  about the cause → make the smallest edit that fixes the cause → re-run.

**Suggested order (easy → hard).** If you want a gentle on-ramp, start with
**Task 5** (pure arithmetic), then **Task 4** and **Task 3**, and finish with
the two hardest — **Task 2** (retry policy) and **Task 1** (the streaming event
loop). The task numbers are just labels; fix them in any order.

**Prereqs:** `uv` installed, and `MISTRAL_API_KEY` in
`/Users/victor.rojo/source/course-automation/.env` for the optional live proofs.
The graded check itself is **offline and free** (it uses the real `mistralai`
SDK types but makes no API calls).

---

## Task 1 — Make the streaming loop never hang (`mais/streaming.py`)  · hardest

- **Objective (Analyze):** Diagnose why a live-progress stream both loses text
  and hangs, and repair the event-fold so it is correct *and* always terminates.
- **Scenario:** A support agent UI streams the model's answer token by token.
  In production, users report the answer appears as a single word, and when a
  turn errors the UI spins forever. You own the fold that turns the raw event
  stream into the final state.
- **Your task:** `fold_events` consumes `client.beta.conversations.start_stream(...)`,
  which yields `ConversationEvents` (each has an `.event` type string and a
  `.data` payload). Two behaviors are wrong — one about how deltas combine, one
  about which events end the loop. Fix both.
- **Hint (direction, not answer):** Read `test_*` for this module. For the text
  bug, ask what should happen to each `message.output.delta` as it arrives — is
  the current code *combining* the deltas or *replacing*? For the hang, list the
  events in `TERMINAL` and check which of them the loop actually handles.
- **Acceptance:** the streaming tests pass; text accumulates and the loop breaks
  on **both** terminal events (`conversation.response.done` and
  `conversation.response.error`).
- **Live proof (optional):** `uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python solution/live_stream.py`

## Task 2 — Fix the retry policy (`mais/concurrency.py`)  · hard

- **Objective (Analyze):** Reason about backoff dynamics and error-class
  handling to stop a client from amplifying an outage.
- **Scenario:** A batch of chat calls runs concurrently. Under a rate limit the
  service gets *worse*, not better, and a plain 400 takes 30 seconds to surface
  the real error. Your retry config is making both problems.
- **Your task:** `build_retry_config` and `should_retry` are each wrong on one
  count — one about how the interval grows between attempts, one about *which*
  HTTP statuses deserve a retry at all. Fix both.
- **Hint (direction, not answer):** For backoff, look at `exponent` and reason
  about what interval sequence `1.0` produces versus what "exponential" means
  under a 429. For `should_retry`, sort HTTP statuses into "retrying will help"
  (transient) vs "retrying just wastes quota and hides the error" (client
  errors) — which classes belong in each bucket?
- **Acceptance:** the concurrency/retry tests pass (backoff grows exponentially;
  only transient failures are retried).
- **Live proof (optional):** `... python solution/live_concurrency.py`

## Task 3 — Fix retrieval quality (`mais/rag.py`)  · medium

- **Objective (Analyze):** Trace wrong retrieval results to two independent
  causes — one in how the corpus is split, one in how similarity is scored.
- **Scenario:** A from-scratch single-corpus RAG (chunk → `mistral-embed` →
  retrieve → ground) keeps returning the wrong passage, so the grounded answer
  is wrong even though the fact is in the corpus.
- **Your task:** Two functions are suspect — one builds the chunks, one scores
  them. Fix both so a straddling fact survives chunking and the closest chunk
  ranks first.
- **Hint (direction, not answer):** Run the two failing tests and read their
  inputs. For chunking, the function takes an `overlap` argument — trace whether
  it is ever used, and picture a fact split across a boundary. For scoring, ask
  what property a *direction* comparison must have that a raw sum-of-products
  lacks when one vector is much longer than another.
- **Acceptance:** the chunking and similarity tests pass (overlap is honored;
  ranking is by direction, not magnitude).
- **Live proof (optional):** `... python solution/live_rag.py` (embeds a corpus,
  retrieves, answers "How many dimensions does mistral-embed produce?" grounded
  in the retrieved text).

## Task 4 — Branch a conversation from the right entry (`mais/entries.py`)  · easy–medium

- **Objective (Analyze):** Verify that a branch starts from the intended turn and
  that the "is this isolated?" check actually proves isolation.
- **Scenario:** `restart(...)` branches a thread into a NEW conversation so you
  can explore an alternative without disturbing the original. In production you
  always seem to branch from the *last* turn, and the isolation guard passes when
  it should fail.
- **Your task:** `pick_branch_entry` selects the wrong entry, and
  `is_isolated_branch` returns the wrong boolean. Fix both.
- **Hint (direction, not answer):** For entry selection, the function takes a
  1-based `occurrence` argument — trace whether the loop respects it or just
  keeps the last match. For isolation, write out what "isolated" means for the
  new vs original conversation id, then compare it to the current condition.
- **Acceptance:** the entry-selection and isolation tests pass (branch from the
  requested occurrence; isolation is true only for a genuinely new conversation).
- **Live proof (optional):** `... python solution/live_restart.py`.

## Task 5 — Get the storage math right (`mais/embedding_cost.py`)  · easiest (good on-ramp)

- **Objective (Analyze):** Turn the documented per-dtype sizing rules into a
  correct byte estimate that a build-vs-quantize decision can rely on.
- **Scenario:** `bytes_per_vector(dim, dtype)` sizes an embedding so an architect
  can choose `output_dimension` + `output_dtype`. The current numbers overstate
  storage for two dtypes, so the team is about to reject quantization on bad math.
- **Your task:** Two dtype sizes are wrong. Fix them so the ratios reflect real
  storage.
- **Hint (direction, not answer):** The module docstring states the true bytes
  (or bits) per component for each dtype. Compare it line by line to the `_BYTES`
  table and the `binary` branch — one entry is off by 2x, one is off by 8x
  because it counts a byte where a *bit* is stored.
- **Acceptance:** the `bytes_per_vector` and storage-ratio tests pass (float = 4
  bytes/component; binary packs 8 components per byte → 32x smaller than float).
- **Live proof (optional):** `... python solution/live_embedding_cost.py`.

---

## When you are done

Running `bash verify/check.sh starter` reports **`12 passed`**. You have
practiced the L300 Analyze move end to end: reading a failing test as an
incident report, forming a root-cause hypothesis, and making the smallest
correct fix — across streaming, retries, retrieval, conversation branching, and
cost math. **Next:** MAIS-400 (Expert) asks you to *design and defend* these
choices under competing constraints, not just repair them.

### Grounding

All SDK calls are grounded in `mistralai==1.9.11` (introspected signatures) and
the pinned docs `platform-docs-public @ a3e0f0c79c5566128ccb7b90e51cc0e7517297da`
(`public/studio-api/knowledge-rag/rag_quickstart.md`, `conversations/`, `agents/`).
No invented methods or parameters.
