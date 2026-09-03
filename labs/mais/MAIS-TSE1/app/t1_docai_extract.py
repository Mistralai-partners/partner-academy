#!/usr/bin/env python
"""Task 1 (SOLUTION) - Document AI structured extraction (the live demo).

Demo point (maps to B4): Document AI is three services behind one call,
`client.ocr.process` - OCR, Annotations, and Document QnA. For "turn documents
into typed data at volume" you use Annotations: pass a `document_annotation_format`
and the response comes back as a JSON object matching your schema, not page text.
That is the credibility moment for a finance or operations buyer - no brittle
regex, no manual entry.

Grounded SDK call (mistralai==2.9.4, verified live):
  - client.ocr.process(model="mistral-ocr-latest", document=ImageURLChunk(...),
        document_annotation_format=response_format_from_pydantic_model(Invoice))
Source: platform-docs-public public/studio-api/document-processing/annotations.md
        + document-processing/overview.md (three Document AI services).
"""
import base64
import json
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.models import ImageURLChunk
from mistralai.extra import response_format_from_pydantic_model
from pydantic import BaseModel, Field

load_dotenv()
MODEL = "mistral-ocr-latest"
ASSET = os.path.join(os.path.dirname(__file__), "..", "assets", "invoice.png")
REQUIRED_KEYS = ("vendor_name", "invoice_number", "total_due")


class Invoice(BaseModel):
    vendor_name: str = Field(description="The company that issued the invoice")
    invoice_number: str = Field(description="The invoice number or id")
    total_due: str = Field(description="The total amount due, including currency")


def _data_uri(path):
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return f"data:image/png;base64,{b64}"


def extract(client, image_path):
    """Annotations return a typed JSON object, not page text."""
    resp = client.ocr.process(
        model=MODEL,
        document=ImageURLChunk(image_url=_data_uri(image_path)),
        document_annotation_format=response_format_from_pydantic_model(Invoice),
    )
    return resp.document_annotation


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    raw = extract(client, ASSET)
    print(f"ANNOTATION: {raw!r}")

    # Acceptance contract: parses as JSON, required keys present and non-empty,
    # and the values match the document (downstream-parseable, not prose).
    obj = json.loads(raw)
    for key in REQUIRED_KEYS:
        assert key in obj and str(obj[key]).strip(), f"missing/empty field: {key}"
    assert "2048" in str(obj["invoice_number"]), f"wrong invoice_number: {obj['invoice_number']}"
    assert "683" in str(obj["total_due"]), f"wrong total_due: {obj['total_due']}"
    print(f"PARSED OK: {obj}")
    print("TASK1 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK1 FAIL: {e}")
        sys.exit(1)
