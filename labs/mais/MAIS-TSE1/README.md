<!-- course-ref -->
**Course:** Mistral AI Studio Tech Sales Essentials (MAIS-TSE1)

# MAIS-TSE1 Lab - Mistral AI Studio Tech Sales Essentials

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> SDK versions, and a troubleshooting table.

Working reference code for **Mistral AI Studio Tech Sales Essentials (MAIS-TSE1)**,
the technical-sales tier. Four production-ready scripts: two live demos
(Document AI extraction, RAG grounding) and two offline scoping exercises
(surface routing, multi-agent judgment). This is **working code you read and
run**, not a broken starter you repair.

Read the scripts before you run anything:

- `app/t1_docai_extract.py` - Document AI extraction (OCR + typed annotations).
- `app/t2_rag_grounding.py` - RAG grounding vs hallucination (embeddings + chat).
- `app/t3_scope_surface.py` - scoping: surface routing + feasibility constraints.
- `app/t4_scope_multiagent.py` - scoping: multi-agent judgment + handoff mode.
- `assets/invoice.png` - the sample document Task 1 extracts from.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/mais/MAIS-TSE1/app
```

Set `MISTRAL_API_KEY` (or a `.env` in this folder) for the live demo scripts.
Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
# 1. Read the working scripts, then run the Document AI demo:
uv run --no-project --with 'mistralai==1.9.11' --with pydantic --with python-dotenv \
  python t1_docai_extract.py

# 2. Run the offline scoping exercises:
uv run --no-project --with 'mistralai==1.9.11' --with pydantic --with python-dotenv \
  python t3_scope_surface.py

# 3. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it confirms the correct SDK imports,
function signatures, and structural properties. A green result never depends on a
live model call.

## Workflows demo

MAIS-TSE1 covers positioning durable Workflows (lesson L2.3). The
`workflows-demo/` subdirectory holds a self-contained Workflows tech-sales demo
with its own verify harness.

## Notes

- Pin `mistralai==1.9.11`: 2.x breaks `from mistralai import Mistral`.
- Tasks 1-2 call the live API; tasks 3-4 are offline decision logic.
