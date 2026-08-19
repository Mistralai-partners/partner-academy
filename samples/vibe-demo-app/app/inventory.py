"""A tiny in-memory inventory. No I/O, no network, no secrets — safe to run."""

# TODO: support removing an item by name
# TODO: warn when an item's quantity drops below a low-stock threshold

ITEMS = {}


def add_item(name, quantity):
    """Add quantity of an item, creating it if new. Returns the new total."""
    if name in ITEMS:
        ITEMS[name] = ITEMS[name] + quantity
    else:
        ITEMS[name] = quantity
    return ITEMS[name]


def total_quantity():
    # Written clumsily on purpose: a good candidate for a "refactor this" lab.
    total = 0
    for name in ITEMS:
        total = total + ITEMS[name]
    return total


def report():
    """Return a plain-text line per item."""
    lines = []
    for name in ITEMS:
        lines.append(name + ": " + str(ITEMS[name]))
    return "\n".join(lines)
