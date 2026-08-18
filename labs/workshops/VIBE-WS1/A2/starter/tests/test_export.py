"""Acceptance tests for the export command.

This file is the contract. Treat it as frozen: the feature must change to make
the tests pass, never the other way around.

- test_csv_format passes against the starter.
- test_json_format fails against the starter, because JSON export does not exist
  yet. It encodes the exact expected JSON shape so it is an objective spec.
"""

import json

from csv_report.data import SAMPLE_ROWS
from csv_report.export import export_rows


def test_csv_format():
    output = export_rows(SAMPLE_ROWS, "csv")
    expected = (
        "id,name,quantity,price\n"
        "1,Widget,10,2.50\n"
        "2,Gadget,5,9.99\n"
        "3,Gizmo,0,14.00\n"
    )
    assert output == expected


def test_json_format():
    output = export_rows(SAMPLE_ROWS, "json")
    expected = json.dumps(SAMPLE_ROWS, indent=2)
    assert output == expected
