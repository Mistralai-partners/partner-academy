"""Order lookups for the sample app.

This module follows the project conventions in src/AGENTS.md: every public
function has a docstring and type hints. It is the "good example" the reviewer
agent should find little to complain about.
"""

_ORDERS: dict[int, list[dict[str, float | str]]] = {
    1: [{"id": "A-100", "total": 42.0}, {"id": "A-101", "total": 8.5}],
    2: [{"id": "B-200", "total": 19.0}],
}


def list_orders_for_user(user_id: int) -> list[dict[str, float | str]]:
    """Return the orders for a user, or an empty list if the user has none."""
    return _ORDERS.get(user_id, [])


def order_total(user_id: int) -> float:
    """Return the summed total of all orders for a user."""
    return sum(float(order["total"]) for order in list_orders_for_user(user_id))
