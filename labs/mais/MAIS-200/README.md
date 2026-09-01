<!-- course-ref -->
**Course:** Mistral AI Studio Intermediate (MAIS-200)

# MAIS-200 Lab - Mistral AI Studio Intermediate

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Intermediate (MAIS-200)**, the L200
(Apply) tier. Eight production-ready SDK scripts you read and run, each
demonstrating a core Studio capability: agents, tool calling, Document AI,
RAG, guardrails, audio transcription, text-to-speech, and observability.
This is **working code you read and run**, not a broken starter you repair.

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
- `app/t6_transcribe_audio.py` - transcribe audio with Voxtral
  (`audio.transcriptions.complete` + diarization + context bias).
- `app/t7_text_to_speech.py` - convert text to speech with Voxtral TTS
  (`audio.voices.list` + `audio.speech.complete` + base64 decode).
- `app/t8_observe_traffic.py` - query the Observability API for production traffic
  (`beta.observability.chat_completion_events.search` + filters). Enterprise tier.

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
uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv python t1_reliable_agent.py

# 2. Run all eight live (each hits the real Mistral API):
for f in t[1-8]_*.py; do
  uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv python "$f"
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
| t6 | B4 - transcribe audio | `audio.transcriptions.complete` + diarization |
| t7 | B4 - text to speech | `audio.voices.list` + `audio.speech.complete` |
| t8 | B5 - observability | `beta.observability.chat_completion_events.search` |

## Notes

- Use `mistralai==2.9.4` (2.x import: `from mistralai.client import Mistral`).
- t6 requires a `sample_audio.mp3` in the `app/` folder for the live run.
- t8 requires Enterprise-tier admin access for live results; passes structurally
  on all accounts.
- All SDK calls are grounded in context7 `/mistralai/client-python` and
  verified live against the real Mistral API.
