# This module is the review target. It works, but it breaks two project
# conventions on purpose (see src/AGENTS.md), so the reviewer agent and the
# security-checklist skill have something real to find:
#   1. calculate_refund has no docstring and no type hints.
#   2. it does not validate its inputs (a negative amount or over-refund slips through).


def calculate_refund(order_total, amount_requested):
    return amount_requested if amount_requested <= order_total else order_total
