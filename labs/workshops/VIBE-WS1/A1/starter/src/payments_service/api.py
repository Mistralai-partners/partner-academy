"""Request handlers and a tiny router for the payments service.

There is no real web framework here. A `request` is a plain dict with a
`method`, a `path`, and a parsed JSON `body`. `route` dispatches to the matching
handler. This keeps the service dependency free while still resembling a small
API surface.
"""

from __future__ import annotations

from typing import Any

from .refunds import RefundError, process_refund
from .store import PaymentStore


def handle_refund(store: PaymentStore, request: dict[str, Any]) -> dict[str, Any]:
    """Handle POST /refunds.

    Expects `request["body"]` to be a dict with `payment_id` and
    `amount_cents`. Returns a response dict with a `status` code and a `body`.
    There is no idempotency key on this path today, so a retried request is
    processed as a brand new refund.
    """
    body = request.get("body") or {}
    payment_id = body.get("payment_id")
    amount_cents = body.get("amount_cents")

    if not payment_id or amount_cents is None:
        return {
            "status": 400,
            "body": {"error": "payment_id and amount_cents are required"},
        }

    try:
        refund = process_refund(store, payment_id, int(amount_cents))
    except RefundError as exc:
        return {"status": 422, "body": {"error": str(exc)}}

    return {
        "status": 201,
        "body": {
            "refund_id": refund.refund_id,
            "payment_id": refund.payment_id,
            "amount_cents": refund.amount_cents,
            "status": refund.status,
        },
    }


def route(store: PaymentStore, request: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a request to a handler based on method and path."""
    method = request.get("method")
    path = request.get("path")
    if method == "POST" and path == "/refunds":
        return handle_refund(store, request)
    return {"status": 404, "body": {"error": "not found"}}
