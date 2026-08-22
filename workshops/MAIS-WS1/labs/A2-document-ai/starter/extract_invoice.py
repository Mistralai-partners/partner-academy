"""Extract structured invoice data from a PDF with Mistral Document AI.

Workshop MAIS-WS1, activity A2 "Document to Structured Data" (starter).

Fill the two TODOs, then prove your work:
  python make_sample_invoice.py
  python extract_invoice.py
  python verify.py

See TASKS.md for guided steps and VERIFY.md for what "done" means.

Run:
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv \
      --with pydantic --with reportlab python extract_invoice.py
"""
import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel

# This repo family imports the client as `from mistralai.client import Mistral`
# (confirmed working against mistralai==2.9.3). Some builds also expose the top-level
# alias `from mistralai import Mistral`. If this import ever fails on the build you
# install, switch to the top-level form.
from mistralai.client import Mistral

SAMPLE_PDF = "sample_invoice.pdf"
OUTPUT_JSON = "extracted.json"


# --- Target schema. Every field must be required for validation to be a real gate. ---
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
    # TODO: add the line-items table field


def build_client() -> Mistral:
    load_dotenv()
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def upload_and_sign(client: Mistral, path: str) -> str:
    """Upload a local PDF for OCR and return a signed URL the API can read."""
    with open(path, "rb") as fh:
        uploaded = client.files.upload(
            file={"file_name": "sample_invoice.pdf", "content": fh},
            purpose="ocr",
        )
    signed = client.files.get_signed_url(file_id=uploaded.id, expiry=24)
    return signed.url


def extract(client: Mistral, document_url: str) -> Invoice:
    # Derive the JSON schema from the Pydantic model. One source of truth.
    schema = Invoice.model_json_schema()

    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": document_url},
        # The inner "schema" key maps to the SDK's JSONSchema.schema_definition
        # (aliased "schema"). "strict": true makes the model honor the schema exactly.
        document_annotation_format={
            "type": "json_schema",
            "json_schema": {
                "schema": schema,
                "name": "invoice",
                "strict": True,
            },
        },
        # table_format allowed values are "markdown" and "html". "markdown" reads
        # cleanly and parses reliably for line items; the Stretch compares "html".
        table_format="markdown",
        include_blocks=False,
    )

    # The whole-document annotation comes back on `document_annotation` as a JSON string.
    annotation = response.document_annotation
    if not annotation:
        raise RuntimeError("OCR returned no document_annotation.")

    # TODO: parse the OCR annotation result through the Invoice schema
    raise NotImplementedError("Return an Invoice parsed from the annotation.")


def main() -> None:
    client = build_client()
    document_url = upload_and_sign(client, SAMPLE_PDF)
    invoice = extract(client, document_url)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(invoice.model_dump(), fh, indent=2)

    print(f"Wrote {OUTPUT_JSON}")
    print(json.dumps(invoice.model_dump(), indent=2))


if __name__ == "__main__":
    main()
