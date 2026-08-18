<!-- course-ref -->
**Course:** Mistral AI Studio Advanced (MAIS-300)

# MAIS-300 Lab — Mistral AI Studio Advanced (hands-on)

Real, runnable lab for **Mistral AI Studio Advanced (MAIS-300, L300)**. Replaces the
in-course click-through with an Analyze-tier **debug-and-tune** exercise against the
Python `mistralai` SDK: streaming event handling, client-side concurrency + retry,
single-corpus RAG, conversation branching, and embedding storage trade-offs.

- `starter/` — begin here. `mais/*.py` has five production bugs (marked `BUG`).
- `solution/` — reference solution + five `live_*.py` scripts that prove each code
  path against the real Mistral API.
- `verify/check.sh <starter|solution>` — deterministic, **offline** acceptance check
  (pytest over the pure logic, using real SDK types; no network, no cost).
- `tasks.md` — the five tasks.

## Run it

```
# graded check (offline, free)
bash verify/check.sh starter      # your progress: fix bugs until 12 passed
bash verify/check.sh solution     # reference: 12 passed

# live proofs (need MISTRAL_API_KEY; cheap: mistral-small-latest, tiny inputs)
cd solution && PYTHONPATH="$PWD" \
  uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv python live_stream.py
```

Done when `bash verify/check.sh starter` reports **12 passed, 0 failed**.

## How verification works

The graded check is deterministic and offline on purpose: it exercises the exact
logic the learner fixes (delta accumulation + terminal handling, retry policy, chunk
overlap + cosine ranking, entry selection + isolation, byte sizing) using the real
`mistralai` event and retry types, so it is reproducible and costs nothing to re-run.
The `live_*.py` scripts separately prove the same code drives the real API end to end.

Grounding: `mistralai==1.9.11`; pinned docs `platform-docs-public @ a3e0f0c7`.
