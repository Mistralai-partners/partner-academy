"""Refund domain logic.

`process_refund` validates a refund request against the stored payment and
records a new refund. There is deliberately no idempotency handling yet: the
same request applied twice creates two distinct refunds.
"""

from __future__ import annotations

import uuid

from .store import PaymentStore, Refund


class RefundError(Exception):
    """Raised when a refund cannot be processed."""


def process_refund(store: PaymentStore, payment_id: str, amount_cents: int) -> Refund:
    """Record a refund against a captured payment.

    Rules enforced today:
      * the payment must exist
      * the amount must be positive
      * total refunds must not exceed the original captured amount

    Note: there is no idempotency key. Calling this twice with the same
    arguments produces two distinct refunds.
    """
    payment = store.get_payment(payment_id)
    if payment is None:
        raise RefundError(f"unknown payment: {payment_id}")
    if amount_cents <= 0:
        raise RefundError("refund amount must be positive")

    already_refunded = store.total_refunded_cents(payment_id)
    if already_refunded + amount_cents > payment.amount_cents:
        raise RefundError("refund exceeds captured amount")

    refund = Refund(
        refund_id=str(uuid.uuid4()),
        payment_id=payment_id,
        amount_cents=amount_cents,
    )
    store.add_refund(refund)
    return refund
