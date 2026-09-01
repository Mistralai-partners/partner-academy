<!-- course-ref -->
**Course:** Mistral AI Studio Expert (MAIS-400)

# MAIS-400 Lab - Mistral AI Studio Expert

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Expert (MAIS-400)**, the L400
(Evaluate/Create) tier. Thirteen production-ready SDK scripts covering batch
operations, caching, retrieval quality, structured output, resilient tool loops,
moderation defense, predicted outputs, realtime transcription, multi-agent
handoffs, client orchestration, expert document AI, voice pipelines, and quality
gates. This is **working code you read and run**, not a broken starter you repair.

Read the scripts before you run anything:

- `app/t1_batch_reconcile.py` - batch API with `custom_id` and reconciliation.
- `app/t2_cache_cost.py` - prompt caching cost diagnosis (offline check).
- `app/t3_embeddings_rerank.py` - embeddings + cosine re-rank + recall@k / MRR.
- `app/t4_structured_output.py` - strict `json_schema` structured output.
- `app/t5_tool_error_loop.py` - function calling with structured error results.
- `app/t6_moderation_defense.py` - Moderation API on the output path.
- `app/t7_predicted_outputs.py` - predicted output for low-latency code edits
  (`chat.complete` with `prediction` param + `codestral-latest`).
- `app/t8_realtime_transcription.py` - real-time transcription latency tuning
  (`audio.realtime.transcribe_stream` + dual-delay comparison). Requires
  `mistralai[realtime]`.
- `app/t9_multi_agent_handoff.py` - multi-hop handoff pipelines
  (`beta.agents.create/update` with `handoffs` wiring + `web_search` tool).
- `app/t10_client_orchestration.py` - client-orchestrated control with function
  results (`handoff_execution="client"` + `FunctionResultEntry` +
  `conversations.append`).
- `app/t11_expert_document_ai.py` - expert Document AI with annotation schemas
  and confidence gating (`ocr.process` + Pydantic + `confidence_scores_granularity`).
- `app/t12_voice_pipelines.py` - voice pipelines under quality and latency
  constraints (`audio.voices.list` + `audio.speech.complete` + streaming).
- `app/t13_quality_gates.py` - regression thresholds on judge scores (pure Python
  gate for CI; Enterprise observability judges/datasets/campaigns documented).

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/mais/MAIS-400/app
```

Set `MISTRAL_API_KEY` in your environment (or a `.env` in this folder) for the
live run steps. Already cloned the repo for another lab? Just `cd` into this
folder instead.

## Read it, run it, check it

```bash
# 1. Read the working scripts, then run one against the live API:
uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv python t1_batch_reconcile.py

# 2. Run all thirteen live:
for f in t{1..13}_*.py; do
  uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv --with pydantic python "$f"
done

# 3. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the correct SDK imports,
function signatures, and API constructor patterns are in place. A green result
never depends on a live model call.

## Notes

- Use `mistralai==2.9.4` (2.x import: `from mistralai.client import Mistral`).
- t8 requires `mistralai[realtime]` (websockets dependency) and a live audio
  source. Passes structurally without them.
- t11 requires `pydantic` for annotation schema validation.
- t13 is pure Python (no API call); it validates the gate pattern offline.
- All SDK calls are grounded in context7 `/mistralai/client-python` and
  verified live against the real Mistral API (2026-09-01).
