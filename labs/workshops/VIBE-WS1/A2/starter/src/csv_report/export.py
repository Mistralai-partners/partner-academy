"""Export logic for csv-report.

`export_rows` turns a list of row dicts into a formatted report string.
Only the CSV format is implemented right now.
"""

import csv
import io


def export_rows(rows, fmt):
    """Render rows in the requested format and return the output as a string.

    Args:
        rows: a list of dicts, each dict a row keyed by column name.
        fmt: the output format. Currently only "csv" is supported.

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

    # TODO: json export format is not implemented
    raise ValueError(f"unsupported format: {fmt}")
