<!-- course-ref -->
**Course:** Mistral AI Studio Advanced (MAIS-300)

# MAIS-300 Lab - Mistral AI Studio Advanced

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Advanced (MAIS-300)**, the L300
(Analyze) tier. A Python package (`mais/`) with five fixed production bugs you
read, trace, and understand. This is **working code you read and run**, not a
broken starter you repair.

The `mais/` package contains the fixed implementations:

- `app/mais/streaming.py` - streaming event fold (accumulates all deltas,
  terminates on error, records tool calls).
- `app/mais/concurrency.py` - retry policy (exponential backoff, transient-only).
- `app/mais/rag.py` - RAG chunking with overlap + cosine similarity retrieval.
- `app/mais/entries.py` - restart from the correct conversation entry.
- `app/mais/embedding_cost.py` - embedding storage cost by quantization type.
- `app/tests/test_lab.py` - offline test suite (uses real SDK types, no network).
- `app/live_*.py` - optional live-API scripts that prove the same code paths.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/mais/MAIS-300/app
```

Set `MISTRAL_API_KEY` (or a `.env` in this folder) for the optional live scripts.
Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
# 1. Read the fixed code in mais/ (start with streaming.py), then run the suite:
uv run --no-project --with 'mistralai==1.9.11' --with pytest \
  python -m pytest tests -q

# 2. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it runs the test suite that exercises
every fixed bug using real SDK types without touching the network. A green result
never depends on a live model call.

## What it covers (course behaviors)

| Module | Bug fixed | Skill |
|---|---|---|
| streaming | fold only kept last delta | accumulate + terminate + record |
| concurrency | retried client errors (4xx) | transient-only + exponential backoff |
| rag | no chunk overlap + dot-product rank | overlap windows + cosine similarity |
| entries | picked wrong branch entry | occurrence-based entry selection |
| embedding_cost | wrong bytes-per-vector | float/int8/binary storage math |

## Notes

- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- The test suite uses real `mistralai.models` event types (no mocks, no fakes).
- The `live_*.py` scripts are optional and need `MISTRAL_API_KEY`.
