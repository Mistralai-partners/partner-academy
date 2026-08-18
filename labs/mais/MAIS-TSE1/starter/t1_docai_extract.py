#!/usr/bin/env python
"""Task 1 (STARTER) - Document AI structured extraction (the live demo).

The demo you run in front of a customer: drop in a scanned document and get
typed JSON back - the exact "reduce manual data entry at volume" story for
finance, insurance, and operations buyers (course B4).

Your job: make `extract()` return a JSON object a downstream accounting system
can parse automatically, with vendor_name, invoice_number, and total_due. The
starter runs plain OCR and returns raw page text, so the acceptance parse fails.

Grounded SDK call (mistralai==1.9.11):
  - client.ocr.process(model="mistral-ocr-latest", document=ImageURLChunk(...),
        document_annotation_format=response_format_from_pydantic_model(<Model>))
Source: platform-docs-public public/studio-api/document-processing/annotations.md
        + document-processing/overview.md (three Document AI services).
"""
import base64
import json
import os
import sys

from dotenv import load_dotenv
from mistralai import ImageURLChunk, Mistral
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
    # BUG: this runs plain OCR and returns the raw recognized page text, so the
    # caller gets prose that json.loads() cannot read - the downstream system
    # needs a typed object, not text.
    # TODO: request a structured annotation so the response is a JSON object
    # shaped like the Invoice contract above.
    resp = client.ocr.process(
        model=MODEL,
        document=ImageURLChunk(image_url=_data_uri(image_path)),
    )
    return resp.pages[0].markdown


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    raw = extract(client, ASSET)
    print(f"ANNOTATION: {raw!r}")

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
