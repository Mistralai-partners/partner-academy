"""Tests for orders.py. The test-writer agent extends these to cover refunds.py."""

from orders import list_orders_for_user, order_total


def test_list_orders_known_user():
    orders = list_orders_for_user(1)
    assert len(orders) == 2
    assert orders[0]["id"] == "A-100"


def test_list_orders_unknown_user():
    assert list_orders_for_user(99) == []


def test_order_total():
    assert order_total(1) == 50.5
    assert order_total(2) == 19.0
    assert order_total(99) == 0.0
