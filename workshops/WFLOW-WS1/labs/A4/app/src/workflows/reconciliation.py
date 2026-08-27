"""A4: nightly reconciliation workflow, determinism-clean.

The two nondeterminism bugs are fixed by keeping the workflow body pure orchestration:

1. Wall-clock time. `datetime.now()` in the body returns a different value on
   replay. It is replaced with `workflows.workflow.now()`, the deterministic
   helper that returns the same value the platform recorded on the first run.
   (Moving the timestamp into an activity is an equally valid fix, because
   activity results are recorded and replayed from history rather than re-run.)

2. Unordered iteration. A `set` has no defined iteration order, so a loop over it
   can diverge on replay. The accounts are de-duplicated with
   `dict.fromkeys(...)` (which preserves insertion order) and then iterated in a
   stable, sorted order, so replay always visits them the same way.

The activity still holds the side effect (reading the ledger). That is the rule:
time, randomness, network, filesystem, and unordered-collection access live in an
activity or a deterministic helper, never in the workflow body.
"""
from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows

from workflows.schedule import SCHEDULE

# The name you trigger and schedule against. verify.py reads this constant so the
# name it triggers always matches the name on @workflow.define.
WORKFLOW_NAME = "reconciliation-workflow"


class ReconciliationInput(BaseModel):
    account_ids: list[str]


class ReconciliationReport(BaseModel):
    run_at: str
    reconciled: dict[str, float]


@workflows.activity(
    # Safe durability defaults. Bound the run time so an unresponsive fetch cannot
    # block indefinitely, and let a transient failure retry with growing backoff.
    # Retries can re-run the activity, so the same input must return the same
    # result.
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def fetch_ledger_balance(account_id: str) -> float:
    """Read one account balance from the ledger.

    Anything that touches the outside world (network, database, filesystem)
    belongs here in an activity, not in the workflow body. This stub returns a
    stable value per account so the lab stays offline and repeatable.
    """
    return float(sum(ord(c) for c in account_id))


@workflows.workflow.define(
    name=WORKFLOW_NAME,
    workflow_display_name="Nightly Reconciliation",
    workflow_description="Reconciles a group of accounts against the ledger.",
    # The schedule is declared on the workflow. The worker registers it with the
    # platform at startup, so schedule changes take effect only after a worker
    # restart. Each schedule passes its own input to the entrypoint.
    schedules=[SCHEDULE],
)
class ReconciliationWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: ReconciliationInput) -> ReconciliationReport:
        # Deterministic time: workflow.now() replays to the recorded value.
        run_at = workflows.workflow.now().isoformat()

        # De-duplicate while preserving insertion order, then iterate in a stable
        # sorted order. Replay always visits the accounts the same way.
        accounts = sorted(dict.fromkeys(input.account_ids))

        reconciled: dict[str, float] = {}
        for account_id in accounts:
            reconciled[account_id] = await fetch_ledger_balance(account_id)

        return ReconciliationReport(run_at=run_at, reconciled=reconciled)
