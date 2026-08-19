# Mistral Partner Academy: Lab Code

Hands-on lab code for the Mistral Partner Academy courses. Each course's lab in the LMS points here.

## Tracks

- `labs/mais/` : Mistral AI Studio (API)
- `labs/vibe/` : Mistral Vibe for Code
- `labs/wflow/`: Mistral AI Studio Workflows

## Layout

`labs/<track>/<COURSE-TIER>/` with `starter/`, `solution/`, `verify/`, plus `tasks.md` and a per-lab `README.md`. Work in `starter/`, check yourself with `verify/`, and compare against `solution/` when you are done.

## Getting the code

```
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/vibe/VIBE-300
```

## Workshops

Facilitated workshop labs live under `workshops/<CODE>-WS1/labs/<A1..>/` with `starter/`, `solution/`, `TASKS.md`, and `VERIFY.md`. Same idea as course labs: work in `starter/`, prove it with the activity's `verify.py`, compare with `solution/`.

## Running the labs

### Prerequisites (all labs)
- **`uv`** (the labs run with `uv run`; no manual venv needed) and **Python 3.11+**.
- A **Mistral account** and an API key exported as `MISTRAL_API_KEY` (or a local `.env` with `MISTRAL_API_KEY=...`). Some MAIS labs use specific models (e.g. `mistral-large-latest`, `voxtral-mini-latest`); if your account lacks one, that task fails with a model error; ask your Mistral contact to enable it.
- Network access to PyPI (the first `uv run` downloads pinned dependencies).
- **On Windows:** run the labs inside **WSL2** or **Git Bash** (the checkers are bash scripts and Vibe Code targets UNIX-like shells).

### The loop (every lab)
1. `cd` into the lab folder.
2. Run the checker against the starter and watch it **fail**; this is expected; it lists the work to do.
3. Do the tasks in `tasks.md` (course labs) / `TASKS.md` (workshops), editing files in `starter/`.
4. Re-run the checker until it passes. `solution/` is the reference if you get stuck.

Pinned SDK versions (do not change them; they are what these labs are verified against):
- MAIS labs: `mistralai==2.9.3` (workshops) / `mistralai==1.9.11` (course labs; see each `verify/check.sh`).
- Workflows labs: course labs pin `mistralai-workflows[mistralai]==3.10.0` (see each `verify/check.sh`); WFLOW workshops run inside a scaffold created by `uvx mistralai-workflows-cli@latest setup`, which provides the workflows SDK (verified against `mistralai-workflows==3.11.0`).

### Workflows (WFLOW) labs need a running worker (two terminals)
A workflow only runs when a **worker** is connected to the platform. `verify/check.sh` is self-contained (it validates logic offline and does not need a worker), but to run a workflow end to end:
1. Scaffold once: `uvx mistralai-workflows-cli@latest setup` (creates the worker + a `Makefile`).
2. Copy the lab's `src/workflows/*` into the scaffold (keep the file layout; do not rename modules).
3. **Terminal 1:** `make start-worker` (leave it running).
4. **Terminal 2:** trigger it: `make execute workflow=<name> input='{...}'` or the lab's `run_client.py` / `verify.py`.
Run one worker at a time. If you start several, the platform can't tell which to use (`AMBIGUOUS_WORKFLOW`); stop the extras.

### Workshops: run the producer before the verifier
Several workshop activities are two-step: a producer script creates an artifact, then `verify.py` checks it. Run the producer first (e.g. `build_agent.py`, `extract_invoice.py`, `transcribe.py`); running `verify.py` alone gives a "file not found" error by design.

### Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `Workflow not found` (404) | worker not running, or workflow name mismatch | start the worker (Terminal 1); confirm `@workflow.define(name=...)` matches what you trigger |
| `AMBIGUOUS_WORKFLOW` (409) | more than one worker/deployment registered the same workflow | run a single worker; stop the others |
| `No such file` / `FileNotFound` | ran the verifier before the producer | run the producer step first (see above) |
| `401 / unauthorized` | `MISTRAL_API_KEY` missing or invalid | export the key or set it in `.env` |
| `model ... not found` / access error | your account lacks that model | request the model/entitlement from your Mistral contact |
| checker passes offline but a live call errors | wrong SDK version | use the pinned versions above; do not upgrade |

## Deployment labs

The self-hosted deployment labs run against a private environment and are not in this repository. Request access from your Mistral partner contact.
