"""Tests for current refund behavior.

These pass against the code as shipped. They document today's behavior,
including the fact that there is no idempotency key: a repeated refund request
creates a second refund. That gap is what ticket PAY-482 asks you to plan.
"""

import pytest

from payments_service import (
    Payment,
    PaymentStore,
    RefundError,
    handle_refund,
    process_refund,
    route,
)


def make_store():
    store = PaymentStore()
    store.add_payment(Payment(payment_id="pay_123", amount_cents=5000, currency="usd"))
    return store


def test_process_refund_records_a_refund():
    store = make_store()
    refund = process_refund(store, "pay_123", 1500)
    assert refund.amount_cents == 1500
    assert refund.payment_id == "pay_123"
    assert store.total_refunded_cents("pay_123") == 1500


def test_process_refund_rejects_unknown_payment():
    store = make_store()
    with pytest.raises(RefundError):
        process_refund(store, "pay_missing", 100)


def test_process_refund_rejects_non_positive_amount():
    store = make_store()
    with pytest.raises(RefundError):
        process_refund(store, "pay_123", 0)


def test_process_refund_rejects_over_refund():
    store = make_store()
    process_refund(store, "pay_123", 4000)
    with pytest.raises(RefundError):
        process_refund(store, "pay_123", 2000)


def test_handle_refund_returns_201():
    store = make_store()
    request = {
        "method": "POST",
        "path": "/refunds",
        "body": {"payment_id": "pay_123", "amount_cents": 2500},
    }
    response = handle_refund(store, request)
    assert response["status"] == 201
    assert response["body"]["amount_cents"] == 2500


def test_handle_refund_validates_body():
    store = make_store()
    response = handle_refund(store, {"method": "POST", "path": "/refunds", "body": {}})
    assert response["status"] == 400


def test_route_dispatches_refund():
    store = make_store()
    request = {
        "method": "POST",
        "path": "/refunds",
        "body": {"payment_id": "pay_123", "amount_cents": 1000},
    }
    assert route(store, request)["status"] == 201


def test_duplicate_request_creates_two_refunds_today():
    # Documents the CURRENT (pre-idempotency) behavior: the same request applied
    # twice creates two refunds. This is exactly the gap ticket PAY-482 closes.
    store = make_store()
    body = {"payment_id": "pay_123", "amount_cents": 1000}
    first = handle_refund(store, {"method": "POST", "path": "/refunds", "body": body})
    second = handle_refund(store, {"method": "POST", "path": "/refunds", "body": body})
    assert first["body"]["refund_id"] != second["body"]["refund_id"]
    assert store.total_refunded_cents("pay_123") == 2000
