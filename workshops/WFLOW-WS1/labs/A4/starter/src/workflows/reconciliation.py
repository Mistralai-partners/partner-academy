"""A4 (starter): nightly reconciliation workflow.

A team put this reconciliation workflow on a nightly schedule. It reconciles a
group of account IDs against the ledger. It passed every manual run, but once it
was scheduled it began to fail on replay with a nondeterminism error, and only
sometimes.

The platform recovers a workflow by REPLAYING its history: it re-runs the
workflow body and expects the same command sequence it saw the first time. So the
workflow body must be deterministic. Any call that reads wall-clock time, draws
randomness, touches the network or filesystem, or iterates an unordered
collection can produce a different value on the second run and make replay
diverge. Work like that belongs in an ACTIVITY (activities are not replayed) or
must use a deterministic helper (workflow.now(), workflow.uuid4(),
workflow.random()).

Two lines in the body below carry a `# BUG:` marker. They run correctly on a
single happy pass and break on replay. Do not trust one green run: reproduce the
failure, trace it from the replay error's step index, and keep the body
deterministic. Full steps are in TASKS.md.
"""
from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows

# The identifier you trigger and schedule against. verify.py and schedule.py both
# read this constant so the name you register on the workflow always matches the
# name you schedule and trigger.
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
)
class ReconciliationWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: ReconciliationInput) -> ReconciliationReport:
        from datetime import datetime

        # BUG: this runs in the workflow body and breaks replay
        run_at = datetime.now().isoformat()

        # De-duplicate the requested accounts. A set has no defined iteration
        # order, so the loop below can visit accounts in a different order on
        # replay. That is the intermittent divergence.
        accounts = set(input.account_ids)

        reconciled: dict[str, float] = {}
        # BUG: this runs in the workflow body and breaks replay
        for account_id in accounts:
            reconciled[account_id] = await fetch_ledger_balance(account_id)

        return ReconciliationReport(run_at=run_at, reconciled=reconciled)
