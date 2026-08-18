"""Tests for the reorder decision logic.

The business rule under test: the threshold is the reorder *trigger point*.
An item needs reordering once its stock reaches the threshold OR drops below it.
The boundary case (stock exactly equal to the threshold) must trigger a reorder.
"""

from inventory_cli.reorder import needs_reorder, reorder_quantity


def test_below_threshold_needs_reorder():
    # Stock is clearly below the trigger point -> reorder.
    assert needs_reorder(2, 5) is True


def test_above_threshold_no_reorder():
    # Stock is comfortably above the trigger point -> do not reorder.
    assert needs_reorder(10, 5) is False


def test_reorder_threshold():
    # Boundary requirement: stock exactly at the threshold IS the trigger point,
    # so the item must be reordered. This is the contract the business relies on.
    assert needs_reorder(5, 5) is True


def test_reorder_quantity_restores_to_target():
    # When well below threshold, order enough to get back to the target level.
    assert reorder_quantity(2, 5, 10) == 8
