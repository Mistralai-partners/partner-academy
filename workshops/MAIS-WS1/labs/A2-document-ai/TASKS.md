# A2 Tasks: Document to Structured Data

## Before you start

- **Behavior you are building:** a pipeline that turns one invoice PDF into a structured
record and refuses to pass that record on unless it is complete and correctly typed.

**Prerequisites:**

- Python 3.10 or later and [uv](https://docs.astral.sh/uv/).
- `MISTRAL_API_KEY` set in your environment or a local `.env` file.

- **Done when:** `verify.py` exits 0 against the record your extractor writes.

Work in the `starter/` folder. The full command to run any script with its
dependencies is:

```
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv \
    --with pydantic --with reportlab python <file>
```

`make_sample_invoice.py` needs only reportlab, and `verify.py` needs only pydantic, so
you can trim the `--with` flags for those two if you like.

---

## Task 0: Prove the checker before you write any code (on-ramp)

- **Objective:** Run the acceptance checker in self-test mode so you know
what a pass and a fail look like before you extract anything.

- **Scenario:** On the job you trust a gate only after you have seen it reject a known-bad
input. A checker that never fails is not a gate.

**Command:**

```
uv run --no-project --with pydantic python verify.py --selftest
```

- **Hint (evidence, not fix):** Read the two blocks it prints. One record passes; one
with `line_items` set to null is rejected. Notice which field the gate names and why.

- **Acceptance:** The self-test exits 0 and reports that the good record passed and the
bad record was rejected.

---

## Task 1: Generate the sample invoice (on-ramp)

- **Objective:** Create the synthetic invoice PDF you will extract from.

- **Scenario:** You need a known input so you can tell a real extraction error apart from
a bad source file. This synthetic invoice has fixed, documented contents.

**Command:**

```
uv run --no-project --with reportlab python make_sample_invoice.py
```

- **Hint (evidence):** Open `sample_invoice.pdf`. Note the supplier, the invoice number,
the three line items, and the total. These are the values your extraction must recover.

- **Acceptance:** `sample_invoice.pdf` exists in the folder.

---

## Task 2: Complete the extraction schema

- **Objective:** Make the `Invoice` model represent the whole invoice, including
its line-item table.

- **Scenario:** Finance reconciles each invoice line against a purchase order. A record
without line items is useless to them, even if the header fields look fine.

- **Hint (evidence, not fix):** Run the starter extractor and read the traceback, then
compare the fields on `Invoice` in `extract_invoice.py` against the fields on the
`Invoice` in `verify.py`. The checker expects a field the extractor does not yet
declare. Look at the `# TODO` marker next to the header fields.

- **Acceptance:** The `Invoice` model carries every field the strict schema in
`verify.py` requires. (Confirmed at the end of Task 3, when the written record passes.)

---

## Task 3: Parse the annotation and write the record

- **Objective:** Turn the OCR annotation into a validated `Invoice` and write it
to `extracted.json`.

- **Scenario:** The API returns the extraction as a JSON string. Passing that string
straight through your strict schema is what converts "the model replied" into "the
record is trustworthy". If a field is missing, you want the failure here, not three
systems downstream.

- **Hint (evidence):** Find the `# TODO: parse the OCR annotation result through the
Invoice schema` marker. The variable `annotation` already holds the JSON string. Pydantic
models have a method that parses a JSON string directly into a validated instance.

**Commands:**

```
# 1. Extract (needs your MISTRAL_API_KEY and sample_invoice.pdf).
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv \
    --with pydantic --with reportlab python extract_invoice.py

# 2. Verify the written record.
uv run --no-project --with pydantic python verify.py
```

- **Acceptance:** `extract_invoice.py` writes `extracted.json`, and `verify.py` exits 0
with "PASS: extracted.json validated against the strict schema."

---

## Stretch: Diagnose a degraded scan

- **Objective:** Feed the extractor a lower-quality document, find which field
breaks, and recover it.

- **Scenario:** Real invoices arrive as faxes, phone photos, and shrunken re-scans. You
need to reason about where OCR loses information and how to adjust.

**Steps:**

- Degrade the input. In a copy of `make_sample_invoice.py`, render the page at a much
   smaller size, or overlay light noise, so the text is harder to read. Regenerate the
   PDF and run the extractor again.
- Read the failure. Run `verify.py` and note which field the gate reports first. Ask
   why that field degraded before the others (small fonts, table cells, and decimals
   are common first casualties).
- Recover it. Try one change at a time and re-verify:
   - Switch the input path from a signed URL to a base64 payload, or the reverse, and
     see whether it changes what OCR reads.
   - Compare `table_format="html"` against `table_format="markdown"` and observe which
     preserves the line-item amounts better for your case.
   - Tighten or annotate the schema (for example, add a `document_annotation_prompt`)
     to steer the model toward the field it dropped.

- **Acceptance:** You can name the field that broke, explain why, and show a change that
makes `verify.py` exit 0 again on the degraded input.
