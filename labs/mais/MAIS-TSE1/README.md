<!-- course-ref -->
**Course:** Mistral AI Studio Tech Sales Essentials (MAIS-TSE1)

# MAIS-TSE1 Lab - Mistral AI Studio Tech Sales Essentials

Real, runnable, dual-modality lab for **Mistral AI Studio Tech Sales Essentials
(MAIS-TSE1)**, the technical-sales tier of the Mistral partner-enablement catalog.
A technical seller's job is to **scope, demo, and answer feasibility** - so this
lab is a runnable demo the seller executes in front of a customer, plus a
scoping/qualification exercise with a deterministic rubric.

It ships for **both delivery modes**:
- **Self-paced** (this repo): `starter/` -> fix the bugs -> `verify/check.sh` is
  green. Done when it reports **4 passed, 0 failed**.
- **Instructor-led / customer-facing:** `FACILITATOR.md` - how to deliver the two
  demos live in a customer session (talk track, timing, what to show, objection
  handling).

- `starter/` - begin here. Each `tN_*.py` has a real defect and a `# BUG/# TODO`.
- `solution/` - reference solutions (all verified live).
- `verify/check.sh <starter|solution>` - runs all four checks; a task passes when
  its script exits 0.
- `assets/invoice.png` - the sample document Task 1 extracts from (self-contained,
  no external URL).
- `tasks.md` - the four tasks, each with objective, scenario, hint, and acceptance.
- `FACILITATOR.md` - the instructor-led / live-demo delivery layer.

## Setup
1. Install [uv](https://docs.astral.sh/uv/).
2. `cp .env.example .env` and set `MISTRAL_API_KEY` (or export it).
3. Run a task or the whole suite (pinned SDK, `mistralai==1.9.11`):
   ```
   bash verify/check.sh starter     # expect failures until you fix the bugs
   bash verify/check.sh solution    # 4 passed, 0 failed
   ```

## What it covers (course behaviors)
| Task | Mode | Course behavior | Capability |
|---|---|---|---|
| 1 | Live demo | B4 - Document AI positioning | Document AI Annotations (typed JSON) |
| 2 | Live demo | B4 - RAG grounding vs hallucination | Embeddings + grounded chat, honest refusal |
| 3 | Scoping | B1/B2/B4/B5 - surface + feasibility | Surface routing + two feasibility constraints |
| 4 | Scoping | B3 - right-sizing + handoffs | Multi-agent judgment + `handoff_execution` mode |

Done when `bash verify/check.sh starter` reports **4 passed, 0 failed**.

## Notes
- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- Tasks 1-2 call the live API with cheap models and tiny inputs; tasks 3-4 are
  offline decision logic (no API calls, no key needed for those two).
- All SDK calls and scoping rules are grounded in the pinned
  `platform-docs-public/public/studio-api/` docs (commit `a3e0f0c7`) and context7
  `/mistralai/client-python`. No invented APIs, paths, or outputs.
- No secrets are committed: `.env` is gitignored; only `.env.example` ships.

## Workflows demo (folded from WFLOW-TSE1)

MAIS-TSE1 covers positioning durable Workflows (lesson L2.3). For the hands-on version, `workflows-demo/` holds a self-contained Workflows tech-sales demo: stand up a durable happy-path workflow, make it interactive, and scope a fit honestly. It keeps its own `tasks.md` and verify harness, so run it separately:

```
bash workflows-demo/verify/check.sh starter   # 4 passed, 0 failed when complete
```
