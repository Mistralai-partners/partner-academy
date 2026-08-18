"""Export logic for csv-report.

`export_rows` turns a list of row dicts into a formatted report string.
Supports the CSV and JSON output formats.
"""

import csv
import io
import json


def export_rows(rows, fmt):
    """Render rows in the requested format and return the output as a string.

    Args:
        rows: a list of dicts, each dict a row keyed by column name.
        fmt: the output format. One of "csv" or "json".

    Returns:
        The formatted report as a string.
    """
    if fmt == "csv":
        output = io.StringIO()
        if rows:
            fieldnames = list(rows[0].keys())
            # lineterminator="\n" keeps output stable across platforms.
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return output.getvalue()

    if fmt == "json":
        return json.dumps(rows, indent=2)

    raise ValueError(f"unsupported format: {fmt}")
