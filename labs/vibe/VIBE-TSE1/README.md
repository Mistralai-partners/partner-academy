<!-- course-ref -->
**Course:** Mistral Vibe for Code - Tech Sales Essentials (VIBE-TSE1)

# VIBE-TSE1 Lab - Mistral Vibe for Code, Tech Sales Essentials

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> versions, and a troubleshooting table.

Working reference code for **Mistral Vibe for Code - Tech Sales Essentials
(VIBE-TSE1)**. For GSI, ISV, and hyperscaler pre-sales consultants. The
completed demo repo (feature + tests + headless PR result) and a filled
scoping/qualification exercise. This is **working code you read and run**, not a
broken starter you repair.

Read the code and artifacts:

- `app/app/vault.py` - the Vault with a working `search()` feature.
- `app/tests/test_search.py` - tests the agent wrote for the search feature.
- `app/pr.json` - the headless PR-style result (CI-ready JSON).
- `app/scoping.json` - completed qualification (verdicts, surface, objection).
- `app/FEATURE.md` - the feature spec Vibe Code implements.
- `app/scenario.md` - the discovery-call scenario.

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/vibe/VIBE-TSE1/app
```

Set `MISTRAL_API_KEY` (or a `.env` in this folder) for the optional live `vibe`
demo. Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
# 1. Read the completed feature (app/vault.py + search), then run the tests:
python3 -m pytest tests -q

# 2. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it checks the feature behavior, test
presence, PR result validity, and the qualification/objection rubric. A green
result never depends on a live model call.

## Notes

- `vibe` CLI >= 2.24 for the optional live demo tasks.
- Scoping tasks need no API key (graded from `scoping.json`).
