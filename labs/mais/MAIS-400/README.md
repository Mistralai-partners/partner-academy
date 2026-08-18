<!-- course-ref -->
**Course:** Mistral AI Studio Expert (MAIS-400)

# MAIS-400 Lab - Mistral AI Studio Expert

Real, runnable SDK lab for **Mistral AI Studio Expert (MAIS-400)**, the L400
(Evaluate/Create) tier of the Mistral partner-enablement catalog. It replaces a
click-through walkthrough with six expert tasks the learner runs against the live
Mistral API using the `mistralai` Python SDK, each with a deterministic
acceptance check.

- `starter/` - begin here. Each `tN_*.py` has a real bug and a `# BUG/# TODO`.
- `solution/` - reference solutions (all verified live).
- `verify/check.sh <starter|solution>` - runs all six checks; a task passes when
  its script exits 0.
- `tasks.md` - the six tasks, with the grounded SDK call and acceptance for each.

## Setup
1. Install [uv](https://docs.astral.sh/uv/).
2. `cp .env.example .env` and set `MISTRAL_API_KEY` (or export it).
3. Run a task or the whole suite (pinned SDK, `mistralai==1.9.11`):
   ```
   bash verify/check.sh starter     # expect failures until you fix the bugs
   bash verify/check.sh solution    # 6 passed, 0 failed
   ```

## What it covers (course behaviors)
| Task | Course behavior | Feature |
|---|---|---|
| 1 | B1 - batch cost + reconciliation | Batch API, `custom_id`, output/error files |
| 2 | B1 - caching cost/diagnosis | Prompt caching (offline; SDK-limited, see task 2) |
| 3 | B4 - retrieval quality | Embeddings, cosine re-rank, recall@k / MRR |
| 4 | B5 - reliable parsing | Strict `json_schema` structured output |
| 5 | B5 - resilient tool loops | Function calling with structured error results |
| 6 | B6 - safety defense-in-depth | Moderation API on the output path |

Done when `bash verify/check.sh starter` reports **6 passed, 0 failed**.

## Notes
- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- Task 2 is an offline structural check; its docstring explains why a live cache
  hit cannot be produced deterministically with the pinned SDK.
- All SDK calls are grounded in the pinned `platform-docs-public/public/studio-api/`
  docs and context7 `/mistralai/client-python`.
