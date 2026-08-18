"""Sample dataset the reporting utility exports.

Values are kept as strings so the CSV and JSON outputs are stable and easy to
assert against in tests. In a real tool this would come from a database or file.
"""

SAMPLE_ROWS = [
    {"id": "1", "name": "Widget", "quantity": "10", "price": "2.50"},
    {"id": "2", "name": "Gadget", "quantity": "5", "price": "9.99"},
    {"id": "3", "name": "Gizmo", "quantity": "0", "price": "14.00"},
]
