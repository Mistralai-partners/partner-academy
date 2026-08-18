# MAIS-TSE1 Lab - Mistral AI Studio Tech Sales Essentials (hands-on)

**Tier:** TSE (Tech Sales Essentials - Apply-dominant, demo and scoping). **What
this lab builds:** the two things a technical seller does in front of a customer -
**run a live capability demo** that earns credibility, and **scope a fit honestly**
(right surface, honest feasibility, no over-engineering). Two tasks are runnable
demos you execute live; two are scoping decisions checked against a rubric. Each
task names its Bloom level; the point is not just to pass the check but to be able
to say *why* to the customer.

**Prereqs:** [uv](https://docs.astral.sh/uv/) installed, a Mistral API key. Copy
`.env.example` to `.env` and set `MISTRAL_API_KEY` (or export it). Work in
`starter/`. Reference solutions are in `solution/`.

**Run one task** (pinned SDK):
```
uv run --no-project --with 'mistralai==1.9.11' --with pydantic --with python-dotenv python starter/t1_docai_extract.py
```
**Run every check:** `bash verify/check.sh starter` - you are **done when it
reports 4 passed, 0 failed**. Each script prints `TASKn PASS` and exits 0 on
success; a task fails until you fix its bug.

**How to work it:** each `tN` file has a real defect marked `# BUG` / `# TODO`.
Read the acceptance for the task, decide the move that satisfies it (and why the
obvious alternative is worse), implement it, then run the check. Tasks 1-2 make
real (cheap) API calls; tasks 3-4 are offline decision logic.

Every SDK call and every scoping rule below is grounded in the pinned
`platform-docs-public/public/studio-api/` docs (commit `a3e0f0c7`) and the
`mistralai` Python SDK (context7 `/mistralai/client-python`). No invented APIs.

---

## Task 1 - Document AI: structured extraction (Apply) - LIVE DEMO
`starter/t1_docai_extract.py`

- **Objective (Apply):** run the Document AI demo that turns a scanned document
  into typed JSON a downstream system can consume.
- **Scenario (why this matters on the job):** a finance or operations buyer spends
  people-hours re-keying invoices. Dropping one into `client.ocr.process` and
  getting back `{vendor_name, invoice_number, total_due}` is the credibility
  moment - no regex, no manual entry, and it scales to volume.
- The starter runs plain OCR and returns raw page text, so the downstream JSON
  parse fails. Switch it to an **Annotations** call so the response is a typed
  object matching the `Invoice` schema.
- **Hint:** the acceptance parses the response as JSON; page text is not JSON.
  The Annotations feature exists exactly for "typed data, not text" - look at what
  parameter turns `ocr.process` from OCR into structured extraction.
- **Acceptance:** the response parses as JSON with non-empty `vendor_name`,
  `invoice_number` (contains `2048`), and `total_due` (contains `683`). SDK:
  `client.ocr.process(model="mistral-ocr-latest", document=ImageURLChunk(...),
  document_annotation_format=response_format_from_pydantic_model(Invoice))`.
  Source: `document-processing/annotations.md`, `overview.md`.

## Task 2 - Grounded RAG with an honest refusal (Apply) - LIVE DEMO
`starter/t2_rag_grounding.py`

- **Objective (Apply):** run the RAG demo that answers from the customer's
  documents and *refuses* - instead of inventing - what the documents do not say.
- **Scenario (why this matters on the job):** the buyer's real fear is
  hallucination. The winning demo is not "look, it answers" - it is "look, it
  answers what it can support **and** says NOT_IN_SOURCES when it cannot." That
  honesty, shown live, closes the trust gap.
- The starter throws away the retrieved context and lets the model answer from
  memory, so it fabricates a warranty period (and, in practice, invents a whole
  different product). Ground the answer in the retrieved passages and forbid
  outside knowledge.
- **Hint:** retrieval is already correct; grounding is not. The model can only be
  faithful to context it is actually given and told to stay inside. Watch the
  starter's live output - it confidently answers a question your corpus never
  covers. That is the behavior to eliminate.
- **Acceptance:** the supported question's answer contains the fact (`38`), and
  the unsupported question returns exactly `NOT_IN_SOURCES`. SDK:
  `client.embeddings.create(model="mistral-embed", ...)` +
  `client.chat.complete(...)`. Source: `knowledge-rag/rag_quickstart.md`,
  `knowledge-rag/embeddings.md`. (Managed alternative to hand-built RAG:
  Libraries - see Task 3, scenario S3.)

## Task 3 - Scope the right surface, call feasibility honestly (Apply) - SCOPING
`starter/t3_scope_surface.py` - **offline**

- **Objective (Apply):** map six customer requirements to the correct AI Studio
  surface, and flag the two that are **not feasible exactly as asked**.
- **Scenario (why this matters on the job):** on a discovery call you must name
  the surface confidently and catch the "you cannot do that the way you described,
  but here is how" moments. Both are credibility; the second is trust.
- Complete the rules in `decide()`. The starter mis-routes any "we want tools"
  ask to Chat Completions and marks everything feasible, so it misses the
  web_search-on-chat-completions and realtime-plus-diarization traps.
- **Hint:** route by the concrete capability first (a document, grounding, or
  transcription need is decisive), then test each request against the two hard
  constraints named in the file. Write the rule; do not hardcode by scenario id.
- **Acceptance:** all six scenarios match the `EXPECTED` (surface,
  feasible_as_asked) rubric. Grounding: web_search/code_interpreter require the
  Conversations/Agents API (`agents/agent-tools/websearch.md`,
  `code_interpreter.md`); Document AI three services (`overview.md`); managed RAG
  = Libraries (`rag_quickstart.md`); realtime is not compatible with `diarize`
  (`audio/speech_to_text/realtime_transcription.md`); stateless single-turn =
  Chat Completions, opt out of storage with `store=False`
  (`conversations/chat-completion.md`, `agents/agents-api.md`).

## Task 4 - Right-size the architecture, choose the handoff mode (Evaluate) - SCOPING
`starter/t4_scope_multiagent.py` - **offline**

- **Objective (Evaluate):** judge four proposed architectures - reject the
  over-engineered ones, and for genuine multi-agent cases pick the correct
  `handoff_execution` mode.
- **Scenario (why this matters on the job):** the customer proposes a five-agent
  chain for a linear, single-domain job. Agreeing is easy and wrong. The honest,
  right-sized recommendation (often a single agent with tools) is the judgment
  that separates a trusted advisor from an order-taker.
- Complete `decide()`. The starter rubber-stamps every proposal as multi-agent
  and always runs handoffs server-side, so it over-engineers the single-domain
  jobs and ignores the human-in-the-loop case.
- **Hint:** ask whether the work spans **distinct specialist domains** or is just
  a chain of deterministic tool calls in one domain. Only genuine multi-agent
  needs a handoff mode - and a human who must inspect/gate each delegation is the
  signal for one specific mode.
- **Acceptance:** all four proposals match the `EXPECTED` (architecture,
  handoff_execution) rubric. Grounding: genuine multi-agent = distinct specialist
  domains; `handoff_execution` = `server` (default, runs internally) or `client`
  (control returns so a human can inspect/gate each delegation)
  (`agents/handoffs.md`, `agents/agents-api.md`).

---

## When you are done

`bash verify/check.sh starter` reports **4 passed, 0 failed**. You have run two
live capability demos (Document AI structured extraction and grounded RAG with an
honest refusal) and made two honest scoping calls (right surface + feasibility,
and right-sized architecture + handoff mode). The TSE bar is being able to *show*
the capability and *scope* the fit without over-promising; if you can narrate each
of these to a customer, you are ready. **Next:** deliver them live - see
`FACILITATOR.md` for the talk track, timing, and objection handling.

**Cost note:** Task 1 makes one `mistral-ocr-latest` call on a tiny local image;
Task 2 makes a handful of `mistral-embed` + `mistral-small-latest` calls with tiny
inputs and low `max_tokens`. Tasks 3-4 make no API calls.

## Workflows demo (positioning durable Workflows, lesson L2.3)

For the Workflows portion of MAIS-TSE1, work `workflows-demo/tasks.md`: run a durable Workflows demo for a customer and scope a fit without over-promising. Verify with `bash workflows-demo/verify/check.sh starter` (done at 4 passed, 0 failed).
