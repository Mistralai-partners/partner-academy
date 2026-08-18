"""In-memory data store for payments and refunds.

This is a teaching stand-in for a real database. Everything lives in
dictionaries on the instance and resets when the process exits. There is no
idempotency-key index today; adding one is the subject of ticket PAY-482.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Payment:
    payment_id: str
    amount_cents: int
    currency: str
    status: str = "captured"


@dataclass
class Refund:
    refund_id: str
    payment_id: str
    amount_cents: int
    status: str = "succeeded"


class PaymentStore:
    """Holds payments and refunds for the lifetime of the process."""

    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}
        self._refunds: dict[str, Refund] = {}
        self._refunds_by_payment: dict[str, list[str]] = {}

    def add_payment(self, payment: Payment) -> None:
        self._payments[payment.payment_id] = payment

    def get_payment(self, payment_id: str) -> Payment | None:
        return self._payments.get(payment_id)

    def add_refund(self, refund: Refund) -> None:
        self._refunds[refund.refund_id] = refund
        self._refunds_by_payment.setdefault(refund.payment_id, []).append(
            refund.refund_id
        )

    def get_refund(self, refund_id: str) -> Refund | None:
        return self._refunds.get(refund_id)

    def refunds_for_payment(self, payment_id: str) -> list[Refund]:
        ids = self._refunds_by_payment.get(payment_id, [])
        return [self._refunds[rid] for rid in ids]

    def total_refunded_cents(self, payment_id: str) -> int:
        return sum(r.amount_cents for r in self.refunds_for_payment(payment_id))
