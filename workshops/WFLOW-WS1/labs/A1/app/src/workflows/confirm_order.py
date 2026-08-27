"""A1: order-confirmation workflow.

An ISV is prototyping an order-confirmation step that must run reliably even if
the process restarts. The durable-workflow mental model is simple: the workflow
orchestrates, and the activity does the work and holds any side effects. Here a
single activity computes the confirmation, and the workflow entrypoint awaits it
and returns the result.
"""
from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows

# The identifier you trigger and schedule against. verify.py reads this constant
# so the name it triggers always matches the name you register on the workflow.
WORKFLOW_NAME = "confirm-order"


class OrderInput(BaseModel):
    order_id: str
    customer: str


@workflows.activity(
    # Safe durability defaults. Always bound the run time so an unresponsive
    # activity cannot block indefinitely, and let a transient failure retry with
    # growing backoff. Retries can re-run the activity, so the same input must
    # always produce the same result.
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def confirm_order(order_id: str, customer: str) -> str:
    """Compute the order confirmation. This is the only place side effects belong."""
    return f"Order {order_id} confirmed for {customer}."


@workflows.workflow.define(
    name=WORKFLOW_NAME,
    workflow_display_name="Confirm Order",
    workflow_description="Computes an order confirmation in a single durable activity.",
)
class ConfirmOrderWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: OrderInput) -> str:
        return await confirm_order(input.order_id, input.customer)
