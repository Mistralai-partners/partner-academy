"""Objective acceptance check for MAIS-WS1 activity A2.

Two modes:
  python verify.py            Validate extracted.json against the strict schema.
  python verify.py --selftest Prove the checker offline on known good and bad records.

"Done" means extracted.json parses through the strict schema with every required
field present, correctly typed, and non-empty. See VERIFY.md.
"""
import json
import sys

from pydantic import BaseModel, ValidationError

OUTPUT_JSON = "extracted.json"


# Strict acceptance schema. This is the gate. It is intentionally required-only:
# no optional fields, so a missing field fails here instead of passing silently.
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class Invoice(BaseModel):
    supplier: str
    invoice_number: str
    invoice_date: str
    total: float
    line_items: list[LineItem]


def check_record(data: dict) -> list[str]:
    """Return a list of failure messages. An empty list means the record passes."""
    problems: list[str] = []

    # 1. Structural and type gate via the strict schema.
    try:
        invoice = Invoice.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(root)"
            problems.append(
                f"{loc}: {err['msg']}. A required field is missing or the wrong type, "
                "so the record cannot be trusted downstream."
            )
        # A record that fails the schema cannot pass the value checks. Stop here.
        return problems

    # 2. Value gates the schema alone does not cover.
    if invoice.total <= 0:
        problems.append(
            f"total is {invoice.total}: a value at or below zero means the amount was "
            "never read. A total must be a real number greater than zero."
        )
    if len(invoice.line_items) == 0:
        problems.append(
            "line_items is empty: the invoice body was dropped. Downstream "
            "reconciliation needs at least one line item."
        )
    for i, item in enumerate(invoice.line_items):
        if not item.description.strip():
            problems.append(
                f"line_items[{i}].description is blank: a line with no description "
                "cannot be matched to a purchase order."
            )
        if item.amount <= 0:
            problems.append(
                f"line_items[{i}].amount is {item.amount}: a line amount at or below "
                "zero breaks the total reconciliation."
            )
    return problems


# Canned fixtures for the offline self-test.
GOOD_FIXTURE = {
    "supplier": "Northwind Traders",
    "invoice_number": "INV-2048",
    "invoice_date": "2026-07-15",
    "total": 300.00,
    "line_items": [
        {"description": "Widget A", "quantity": 10, "unit_price": 12.50, "amount": 125.00},
        {"description": "Widget B", "quantity": 4, "unit_price": 30.00, "amount": 120.00},
        {"description": "Service fee", "quantity": 1, "unit_price": 55.00, "amount": 55.00},
    ],
}

# The classic silent failure: extraction "succeeded" but the table came back null.
BAD_FIXTURE = {
    "supplier": "Northwind Traders",
    "invoice_number": "INV-2048",
    "invoice_date": "2026-07-15",
    "total": 300.00,
    "line_items": None,
}


def selftest() -> int:
    print("[selftest] Checking a known-good record...")
    good_problems = check_record(GOOD_FIXTURE)
    if good_problems:
        print("  FAIL: the good record should pass but did not:")
        for p in good_problems:
            print(f"    - {p}")
        return 1
    print("  PASS: good record validated, as expected.")

    print("[selftest] Checking a known-bad record (line_items is null)...")
    bad_problems = check_record(BAD_FIXTURE)
    if not bad_problems:
        print(
            "  FAIL: the bad record passed. The checker is not a real gate. "
            "A loose or optional schema rubber-stamps a missing field. "
            "Tighten the schema so a null table is rejected."
        )
        return 1
    print("  PASS: bad record rejected, as expected. The gate reports:")
    for p in bad_problems:
        print(f"    - {p}")
    print("[selftest] OK: the checker distinguishes good from bad.")
    return 0


def verify_file() -> int:
    try:
        with open(OUTPUT_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(
            f"{OUTPUT_JSON} not found. Run the extractor first so there is a record "
            "to check. Done means this file validates against the strict schema."
        )
        return 1
    except json.JSONDecodeError as exc:
        print(f"{OUTPUT_JSON} is not valid JSON: {exc}. The extractor wrote a broken file.")
        return 1

    problems = check_record(data)
    if problems:
        print(f"FAIL: {OUTPUT_JSON} did not pass the acceptance gate.")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nRead each reason above as an incident report: it names the field and why "
            "a downstream system would break. A common trap is a loose or optional "
            "schema that passes while a field is silently null. Make the extraction "
            "produce a complete record, then run this check again."
        )
        return 1

    print(f"PASS: {OUTPUT_JSON} validated against the strict schema.")
    print("Required fields are present, correctly typed, and non-empty.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return verify_file()


if __name__ == "__main__":
    sys.exit(main())
