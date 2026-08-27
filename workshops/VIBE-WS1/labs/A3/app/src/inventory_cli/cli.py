"""Command-line interface for inventory-cli."""

import argparse
import sys
from typing import Optional, Sequence

from inventory_cli.reorder import needs_reorder, reorder_quantity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inventory-cli",
        description="Decide whether a stocked item needs reordering.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    reorder = subparsers.add_parser(
        "reorder",
        help="Check reorder status for one item.",
    )
    reorder.add_argument("--stock", type=int, required=True, help="Units on hand.")
    reorder.add_argument(
        "--threshold", type=int, required=True, help="Reorder trigger point."
    )
    reorder.add_argument(
        "--target",
        type=int,
        default=None,
        help="Desired stock level to restore up to (defaults to 2x threshold).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "reorder":
        target = args.target if args.target is not None else args.threshold * 2
        if needs_reorder(args.stock, args.threshold):
            qty = reorder_quantity(args.stock, args.threshold, target)
            print(f"REORDER: order {qty} units (stock {args.stock} <= threshold {args.threshold})")
        else:
            print(f"OK: no reorder needed (stock {args.stock} > threshold {args.threshold})")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
