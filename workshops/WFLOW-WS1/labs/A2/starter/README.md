# A2 Starter - resilient_confirm

This is the starter for WFLOW-WS1 activity A2, "Make It Resilient: Timeouts,
Retries, and Heartbeats."

## Drop it into a scaffold

1. Create a scaffold: `uvx mistralai-workflows-cli@latest setup`.
2. Copy `src/workflows/resilient_confirm.py` into the scaffold's
   `src/workflows/`. The worker auto-discovers it.
3. Copy `verify.py` into the scaffold root, next to the Makefile.
4. Export `MISTRAL_API_KEY`.

## The fault injector is intentional

`resilient_confirm.py` ships a provided fault injector that simulates a flaky
downstream service. It errors on the first attempts and then wedges on the next
one. This is the scenario. Do not remove it. Your task is to make the activity
survive it by adding durability configuration and heartbeats, not to delete the
fault.

## What to do

Follow `../TASKS.md`. Verify with `python verify.py --selftest` (offline) and
then `python verify.py` (live, against a running worker). See `../VERIFY.md` for
what green means.
