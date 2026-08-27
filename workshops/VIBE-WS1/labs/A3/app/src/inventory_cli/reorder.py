"""Reorder decision logic.

The reorder rule: an item's ``threshold`` is the trigger point. When stock
reaches the threshold or drops below it, the item needs to be reordered.
"""


def needs_reorder(stock_level: int, threshold: int) -> bool:
    """Return True when the item should be reordered.

    An item should be reordered once its stock reaches the reorder trigger
    point. The threshold is that trigger point.
    """
    # BUG: threshold off by one at the boundary
    return stock_level < threshold


def reorder_quantity(stock_level: int, threshold: int, target: int) -> int:
    """Return how many units to order to restore stock to ``target``.

    Returns 0 when no reorder is needed. Otherwise returns the number of units
    required to bring the current stock back up to ``target`` (never negative).
    """
    if not needs_reorder(stock_level, threshold):
        return 0
    return max(0, target - stock_level)
