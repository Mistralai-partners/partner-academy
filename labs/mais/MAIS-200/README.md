<!-- course-ref -->
**Course:** Mistral AI Studio Intermediate (MAIS-200)

# MAIS-200 Lab - Mistral AI Studio Intermediate

Real, runnable SDK lab for **Mistral AI Studio Intermediate (MAIS-200)**, the L200
(Apply) tier of the Mistral partner-enablement catalog. It replaces click-through worked examples
with five everyday build tasks the learner runs against the live Mistral API using
the `mistralai` Python SDK, each with a deterministic acceptance check.

- `starter/` - begin here. Each `tN_*.py` has one clearly marked `# TODO` where the
  real SDK work is missing.
- `solution/` - reference solutions (all verified live).
- `verify/check.sh <starter|solution>` - runs all five checks; a task passes when
  its script exits 0.
- `tasks.md` - the five tasks, each with objective, scenario, hint, acceptance, and
  the grounded SDK call.
- `FACILITATOR.md` - instructor-led facilitation layer (agenda, demo checkpoints,
  discussion prompts, pitfalls).

## Setup
1. Install [uv](https://docs.astral.sh/uv/).
2. `cp .env.example .env` and set `MISTRAL_API_KEY` (or export it).
3. Run a task or the whole suite (pinned SDK, `mistralai==1.9.11`):
   ```
   bash verify/check.sh starter     # expect failures until you complete the TODOs
   bash verify/check.sh solution    # 5 passed, 0 failed
   ```

## What it covers (course behaviors)
| Task | Course behavior | Feature |
|---|---|---|
| 1 | B1 - reliable agent | `beta.agents.create` with `instructions` + `completion_args` |
| 2 | B1 - tools + state | function tool + `FunctionResultEntry` + `conversations.append` |
| 3 | B2 - document extraction | `ocr.process` + `document_annotation_format` (Pydantic) |
| 4 | B3 - RAG knowledge base | `mistral-embed` + cosine retrieval + grounded/refuse |
| 5 | B5 - guardrail | `classifiers.moderate` input gate |

Done when `bash verify/check.sh starter` reports **5 passed, 0 failed**.

## Notes
- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- All SDK calls are grounded in the pinned `platform-docs-public/public/studio-api/`
  docs (`a3e0f0c79c5566128ccb7b90e51cc0e7517297da`) and context7
  `/mistralai/client-python`. No invented methods or parameters.
- Two documented parameters are taught but not called because the pinned SDK does
  not expose them: `table_format="html"` (Task 3) and the inline `guardrails`
  parameter (Task 5). Each file explains the gap and uses the supported path.
- B4 (Voxtral transcription + TTS) is deferred: see the coverage note in `tasks.md`.
