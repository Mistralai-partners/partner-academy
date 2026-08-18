# A2 Acceptance Contract

This file defines what "done" means for activity A2 and how to read the checker.

## What done means

You are done when `verify.py` exits 0. That happens only when `extracted.json`:

- Parses as JSON.
- Validates against the strict `Invoice` schema: `supplier`, `invoice_number`,
   `invoice_date`, `total`, and `line_items` are all present and correctly typed.
- Passes the value gates that a schema alone does not cover:
   - `total` is a number greater than zero.
   - `line_items` is a non-empty list.
   - Each line item has a non-blank `description` and an `amount` greater than zero.

The strict schema is intentionally required-only. There are no optional fields, so a
missing field fails the check instead of slipping through.

## How to run it

```
# Validate the record your extractor wrote.
uv run --no-project --with pydantic python verify.py

# Prove the checker offline, with no API call, on a known-good and a known-bad record.
uv run --no-project --with pydantic python verify.py --selftest
```

## How to read the output

- **PASS** and exit 0: the record is complete and correctly typed. You are done.
- **FAIL** and exit 1: the checker prints one line per problem. Read each line as an
  incident report. It names the exact field and states why a downstream system would
  break on it. Fix the extraction so the record is complete, then run the check again.
- **File not found** and exit 1: run the extractor first so there is a record to check.

## The common failure: a silently missing field

The failure to watch for is a loose or optional schema that passes while a field is
null. Picture an extraction that returns the header fields but sets `line_items` to
null. If your schema treats `line_items` as optional, validation rubber-stamps the
record, and finance later discovers invoices with no line items to reconcile.

Diagnose it this way:

- The header looks correct, but a downstream consumer reports empty or missing data.
- You inspect `extracted.json` and find the field is present but null, or absent.
- The root cause is the schema, not the model: an optional field cannot be a gate.
- The fix is to make the field required so validation rejects the null. The self-test
   demonstrates exactly this: it feeds a record with `line_items` set to null and
   confirms the strict schema rejects it.
