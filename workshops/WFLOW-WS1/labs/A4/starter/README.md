# A4 starter: Diagnose a Nondeterminism Failure in a Scheduled Workflow

This is the A4 starter. It is meant to fail until you fix it.

## What to do

1. Create a scaffold with `uvx mistralai-workflows-cli@latest setup` and run
   `uv add mistralai-workflows`.
2. Copy `src/workflows/reconciliation.py` and `src/workflows/schedule.py` into the
   scaffold's `src/workflows/`, and copy `verify.py` to the scaffold root.
3. Run `uv run python verify.py --selftest`. It fails on purpose. That is your
   starting point.
4. Follow `TASKS.md`.

## Notes

- The `# BUG: this runs in the workflow body and breaks replay` markers in
  `reconciliation.py` are intentional. They flag calls that run correctly on a
  single pass and break on replay.
- The `TODO` markers in `schedule.py` are intentional. The schedule definition is
  incomplete and nothing attaches it to the workflow yet.
- `[VERIFY]` comments mark surface that is environment-specific or not confirmed in
  the current live docs (for example the schedule-to-deployment binding). Confirm
  those against your own environment before you rely on them.
- What green means is in `../VERIFY.md`.
