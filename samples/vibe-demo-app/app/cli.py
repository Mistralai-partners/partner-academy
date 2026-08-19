"""Minimal CLI for the demo inventory. Run: python -m app.cli"""

from app.inventory import add_item, total_quantity, report


def main():
    add_item("widgets", 3)
    add_item("gadgets", 5)
    add_item("widgets", 2)
    print(report())
    print("total:", total_quantity())


if __name__ == "__main__":
    main()
