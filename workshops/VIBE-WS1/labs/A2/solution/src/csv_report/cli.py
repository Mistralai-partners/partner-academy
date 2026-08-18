"""Command-line interface for csv-report."""

import argparse

from csv_report.data import SAMPLE_ROWS
from csv_report.export import export_rows


def build_parser():
    parser = argparse.ArgumentParser(prog="csv-report")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export the sample dataset")
    export_parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format for the report",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        print(export_rows(SAMPLE_ROWS, args.format), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
