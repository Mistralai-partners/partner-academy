# A2: Document to Structured Data

Workshop MAIS-WS1, activity A2. Practitioner tier (L200 to L300).

## Scenario

You work at a GSI onboarding a customer's supplier invoices. Finance cannot key in
every invoice by hand, and downstream systems reject anything that is not clean and
complete. Your job: take one invoice PDF, read it with OCR, extract a fixed set of
fields into a structured record, and prove that record is trustworthy before it moves
on.

## What you build

A small pipeline that:

1. Uploads a PDF and OCRs it with Mistral Document AI (`mistral-ocr-latest`).
2. Extracts a fixed field set (supplier, invoice number, date, total, line items)
   using a strict JSON schema.
3. Validates the result against that schema so a missing or malformed field fails
   loudly instead of leaking downstream.

## Prerequisites

- Python 3.10 or later and [uv](https://docs.astral.sh/uv/).
- A Mistral API key. Set `MISTRAL_API_KEY` in your environment or a local `.env` file.
- No invoice file needed: you generate a deterministic synthetic one in step 1.

Setup takes under 5 minutes. Every command uses `uv run --no-project`, so you do not
manage a virtual environment.

## Done when checks pass

You are done when `verify.py` exits 0. That means `extracted.json` validates against
the strict schema with every required field present, correctly typed, and non-empty.
See `VERIFY.md` for the full acceptance contract.

## Layout

- `starter/` has the code with two gaps to fill. Start here.
- `solution/` has the complete reference. Check it after you try.
- `TASKS.md` walks you through the work, easy to hard.
- `VERIFY.md` defines what "done" means and how to read the checker output.

## What you learn and where next

You learn why structured extraction is only as good as the schema that gates it: a
loose or optional schema will happily pass a record with a silently missing field. A
strict schema turns validation into a real gate.

Next: MAIS-200 covers the Document AI and structured-output building blocks in depth;
MAIS-300 extends this into multi-step and cross-capability pipelines.
