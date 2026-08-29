<!-- course-ref -->
**Course:** Mistral AI Studio Intermediate (MAIS-200)

# MAIS-200 Lab - Mistral AI Studio Intermediate

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Intermediate (MAIS-200)**, the L200
(Apply) tier. Five production-ready SDK scripts you read and run, each
demonstrating a core Studio capability: agents, tool calling, Document AI,
RAG, and guardrails. This is **working code you read and run**, not a broken
starter you repair.

Read the scripts before you run anything:

- `app/t1_reliable_agent.py` - build a reliable agent (`beta.agents.create` with
  `instructions` + `completion_args`).
- `app/t2_tools_function_result.py` - give an agent a tool and return its result
  (`FunctionResultEntry` with matching `tool_call_id`).
- `app/t3_document_to_structured.py` - extract structured data from a document
  (`ocr.process` + Pydantic `document_annotation_format`).
- `app/t4_rag_knowledge_base.py` - build a small RAG knowledge base
  (`mistral-embed` + cosine retrieval + grounded answer).
- `app/t5_guardrails_moderation.py` - guardrail inputs with the Moderation API
  (`classifiers.moderate` input gate).

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/mais/MAIS-200/app
```

Set `MISTRAL_API_KEY` in your environment (or a `.env` in this folder) for the
live run steps. Already cloned the repo for another lab? Just `cd` into this
folder instead.

## Read it, run it, check it

```bash
# 1. Read the working scripts (start with t1), then run one against the live API:
uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python t1_reliable_agent.py

# 2. Run all five live (each hits the real Mistral API):
for f in t[1-5]_*.py; do
  uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python "$f"
done

# 3. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the correct SDK imports,
function signatures, and API constructor patterns are in place. A green result
never depends on a live model call.

## What it covers (course behaviors)

| Script | Course behavior | Feature |
|---|---|---|
| t1 | B1 - reliable agent | `beta.agents.create` with `instructions` + `completion_args` |
| t2 | B1 - tools + state | function tool + `FunctionResultEntry` + `conversations.append` |
| t3 | B2 - document extraction | `ocr.process` + `document_annotation_format` (Pydantic) |
| t4 | B3 - RAG knowledge base | `mistral-embed` + cosine retrieval + grounded/refuse |
| t5 | B5 - guardrail | `classifiers.moderate` input gate |

## Notes

- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- All SDK calls are grounded in the pinned `platform-docs-public` docs and
  context7 `/mistralai/client-python`. No invented methods or parameters.
