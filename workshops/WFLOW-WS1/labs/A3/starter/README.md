# A3 starter - Interact With a Running Workflow

This is the A3 starter. It is a runnable skeleton, not a blank page: the
workflow loads and its three interaction handlers are discoverable, but two of
them are wired to the wrong behavior on purpose.

## Get going

1. Create a scaffold: `uvx mistralai-workflows-cli@latest setup`, then
   `uv add mistralai-workflows`.
2. Drop these files into the scaffold so `src/workflows/triage_workflow.py`
   lands under `src/workflows/` and `verify.py` sits at the scaffold root.
3. Baseline it: `python verify.py --selftest`.
4. Follow `TASKS.md` to fix the query, wake the workflow on a signal, and
   implement the update. Then run it live per `VERIFY.md`.

Your goal: match the right interaction primitive (signal, query, update) to each
need so the workflow's state reflects every interaction. Start with `TASKS.md`.
