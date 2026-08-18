# MAIS-200 Lab - Mistral AI Studio Intermediate (hands-on)

**Tier:** L200 (Intermediate - Apply). **Behavior this lab grades:** build the
common, everyday AI Studio features by hand - a reliable tool-using agent with
managed conversation state, a Document AI extraction, a small RAG knowledge base,
and a build-time safety guardrail - well enough to be productive on real client
work without hand-holding. Each task names its Bloom level; the point is to *use
the SDK for real work*, not to recognize the right answer.

**Prereqs:** [uv](https://docs.astral.sh/uv/) installed, a Mistral API key.
Copy `.env.example` to `.env` and set `MISTRAL_API_KEY` (or export it). Work in
`starter/`. Reference solutions are in `solution/`.

**Run one task** (pinned SDK):
```
uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python starter/t1_reliable_agent.py
```
**Run every check:** `bash verify/check.sh starter` - you are done when it reports
**5 passed, 0 failed**. Each script prints `TASKn PASS` and exits 0 on success; a
task fails until you complete it.

**How to work it:** each `tN` file has one clearly marked `# TODO` where the real
SDK work is missing. Read the task's Objective and Acceptance, complete the call
with the grounded SDK usage shown in the file's docstring, then run the check. The
TODO names the *task and its symptom*, not the code - writing the correct SDK call
is the Apply skill this lab grades.

Every SDK call below is grounded in `platform-docs-public/public/studio-api/`
(pinned `a3e0f0c79c5566128ccb7b90e51cc0e7517297da`) and the `mistralai` Python SDK
(context7 `/mistralai/client-python`). No invented methods or parameters.

---

## Task 1 - Build a reliable agent (Apply)  ·  `t1_reliable_agent.py`  ·  covers B1

- **Objective (Apply):** build an agent that behaves predictably - give it standing
  behavior and safe, deterministic completion settings.
- **Scenario:** you are standing up a support triage bot for a client. It must
  answer in a consistent short format on every turn, and its output must be
  repeatable and cost-bounded so QA can rely on it.
- **What to do:** the starter creates an agent with no `instructions` and default
  completion settings, so it has no standing behavior and its output is neither
  deterministic nor length-capped. Give it `instructions` and
  `completion_args={"temperature": 0, "max_tokens": ...}`.
- **Hint (direction, not answer):** look at what the acceptance checks read off the
  returned agent - `agent.instructions`, `agent.completion_args.temperature`,
  `.max_tokens`. Those are exactly the build-time settings you must supply.
- **Acceptance:** the agent carries your standing behavior, `temperature == 0`,
  `max_tokens` is set, and a turn returns a non-empty `message.output`.
- **Grounded SDK:** `client.beta.agents.create(model, name, instructions,
  completion_args=...)`; `client.beta.conversations.start(agent_id, inputs)`.

## Task 2 - Tools and function results (Apply)  ·  `t2_tools_function_result.py`  ·  covers B1

- **Objective (Apply):** close a tool loop by returning a function's result into
  the conversation so the model can finish.
- **Scenario:** your agent answers order questions from a system it cannot see. The
  model asks for `get_order_status`; if you do not hand the answer back correctly,
  the conversation hangs on the tool call and the customer never gets a reply.
- **What to do:** the starter returns the unfinished response while the last output
  is still a `function.call`. Execute the requested function and return its result
  to the conversation with a `FunctionResultEntry` whose `tool_call_id` matches the
  call the model made, then return the final response.
- **Hint (direction, not answer):** read `resp.outputs[-1]` - it carries `.name`,
  `.arguments`, and `.tool_call_id`. The result you append must reference that same
  `tool_call_id`, or the model will not recognize which call it answers.
- **Acceptance:** the final output type is `message.output` and its content
  reflects the real status (`shipped`).
- **Grounded SDK:** `FunctionResultEntry(tool_call_id, result)`;
  `client.beta.conversations.append(conversation_id, inputs=[entry])`.

## Task 3 - From a document to structured data (Apply)  ·  `t3_document_to_structured.py`  ·  covers B2

- **Objective (Apply):** extract typed fields from a document with Document AI, not
  just raw text.
- **Scenario:** a downstream service needs a document's language, title, and
  keywords as typed fields it can index. Plain OCR text will not do - you need a
  structured annotation shaped by your schema.
- **What to do:** the starter runs plain OCR, so `document_annotation` comes back
  empty. Pass your Pydantic model as the annotation format so the OCR result
  carries a `document_annotation` that parses into `DocMeta`.
- **Hint (direction, not answer):** the docstring imports
  `response_format_from_pydantic_model` - that helper turns a Pydantic model into
  the format `ocr.process` needs. Look at which parameter takes it.
- **Acceptance:** `response.document_annotation` is non-empty and validates as
  `DocMeta` with a language and title.
- **Grounded SDK:** `client.ocr.process(model="mistral-ocr-latest", document=...,
  document_annotation_format=response_format_from_pydantic_model(DocMeta),
  pages=[0])`.
- **Note:** `table_format="html"` (preserves merged-cell tables) is documented but
  not exposed in the pinned SDK, so it is taught in the file, not called.

## Task 4 - Build a small RAG knowledge base (Apply)  ·  `t4_rag_knowledge_base.py`  ·  covers B3

- **Objective (Apply):** implement the from-scratch RAG retrieval step so answers
  are grounded in the right passage - and refuse when the fact is absent.
- **Scenario:** you are building a small knowledge base over internal notes. If
  retrieval returns the wrong chunk, the grounded answer is confidently wrong; if
  it cannot find the fact, the bot must refuse rather than invent one.
- **What to do:** the starter's `retrieve` returns the first chunk every time.
  Rank the corpus against the query embedding and return the best match by cosine
  similarity, so the right chunk is retrieved and the below-threshold case refuses.
- **Hint (direction, not answer):** a `cosine` helper is already provided. Ask what
  property a *direction* comparison has that returning a fixed index does not, and
  which chunk index the present-fact query should select.
- **Acceptance:** the present-fact query retrieves chunk index 1 and the grounded
  answer contains `1024`; the absent-fact query scores below threshold and refuses.
- **Grounded SDK:** `client.embeddings.create(model="mistral-embed", inputs=[...])`;
  `client.chat.complete(model, messages, temperature=0)`.
- **Note:** the managed alternative is the Document Library / built-in document
  tool, which handles chunk/embed/retrieve for you.

## Task 5 - Guardrails at build time (Apply)  ·  `t5_guardrails_moderation.py`  ·  covers B5

- **Objective (Apply):** put a moderation guardrail in front of the model so unsafe
  inputs are blocked before they reach it.
- **Scenario:** your assistant is public. A benign question must go through, but a
  request for harmful instructions must be blocked at the door.
- **What to do:** the starter's gate lets everything through. Call the Moderation
  service on the input and decide allow/block from the flagged policy categories.
- **Hint (direction, not answer):** `results[0].categories` is a map of category to
  boolean. What does "allowed" mean in terms of how many categories are flagged?
- **Acceptance:** the benign input is allowed; the harmful input is blocked.
- **Grounded SDK:** `client.classifiers.moderate(model="mistral-moderation-latest",
  inputs=[...])`.
- **Note (production path):** the recommended production guardrail is declared
  inline via the `guardrails` parameter (`moderation_llm_v2` config, inheritable
  per agent). That parameter is not exposed in the pinned SDK, so this task builds
  the same protection with the Moderation API it is built on. Taught in the file.

---

## When you are done

`bash verify/check.sh starter` reports **5 passed, 0 failed**. You have built five
everyday AI Studio features by hand - a reliable agent, a closed tool loop,
structured document extraction, a grounded-and-refusing RAG, and an input
guardrail - each proven by a runnable check. **Next:** MAIS-300 (Advanced) hands
you a system where these same behaviors are subtly broken and asks you to trace
each failure to its root cause and fix it.

## Coverage and notes

- **Behaviors covered:** B1 (Tasks 1-2), B2 (Task 3), B3 (Task 4), B5 (Task 5).
- **Not covered here:** B4 (Voxtral offline transcription + TTS). It needs an audio
  fixture and its output is not deterministically checkable within the cheap,
  self-contained bar this lab holds, so it is deferred rather than faked.
- **Cost note:** every task uses small models (`mistral-small-latest`,
  `mistral-embed`, `mistral-ocr-latest` on one page, `mistral-moderation-latest`),
  tiny inputs, and low `max_tokens`.
