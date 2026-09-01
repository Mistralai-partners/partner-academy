<!-- course-ref -->
**Course:** Mistral AI Studio Expert (MAIS-400)

# MAIS-400 Lab - Mistral AI Studio Expert

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Expert (MAIS-400)**, the L400
(Evaluate/Create) tier. Six production-ready SDK scripts covering batch
operations, caching, retrieval quality, structured output, resilient tool loops,
and moderation defense. This is **working code you read and run**, not a broken
starter you repair.

Read the scripts before you run anything:

- `app/t1_batch_reconcile.py` - batch API with `custom_id` and reconciliation.
- `app/t2_cache_cost.py` - prompt caching cost diagnosis (offline check).
- `app/t3_embeddings_rerank.py` - embeddings + cosine re-rank + recall@k / MRR.
- `app/t4_structured_output.py` - strict `json_schema` structured output.
- `app/t5_tool_error_loop.py` - function calling with structured error results.
- `app/t6_moderation_defense.py` - Moderation API on the output path.

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
uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python t1_batch_reconcile.py

# 2. Run all six live:
for f in t[1-6]_*.py; do
  uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python "$f"
done

# 3. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the correct SDK imports,
function signatures, and API constructor patterns are in place. A green result
never depends on a live model call.

## Notes

- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- Task 2 is an offline structural check (prompt caching cannot be produced
  deterministically with the pinned SDK).
