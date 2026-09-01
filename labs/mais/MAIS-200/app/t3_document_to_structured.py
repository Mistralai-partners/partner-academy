#!/usr/bin/env python
"""Task 3 (SOLUTION) - Turn a document into structured data with Document AI.

Behavior (maps to MAIS-200 B2, FKC Q5/Q6): plain OCR gives you text; to get typed
fields a downstream system can rely on, pass a Pydantic model as
`document_annotation_format`. The OCR result then carries a `document_annotation`
JSON string that parses straight into your schema.

Grounded production note (grounded, not on the pinned SDK): for documents with
merged-cell tables, `ocr.process(..., table_format="html")` preserves table
structure instead of flattening it. That parameter is documented (basic_ocr.md)
but is not exposed in mistralai==2.9.4, so it is omitted from the runnable call
below and taught here only.

Grounded SDK calls (mistralai==2.9.4, verified live):
  - from mistralai.extra import response_format_from_pydantic_model
  - client.ocr.process(model="mistral-ocr-latest",
        document=DocumentURLChunk(document_url=...),
        document_annotation_format=response_format_from_pydantic_model(Model),
        pages=[0])
        -> response.document_annotation  (JSON string matching Model)
Source: platform-docs-public public/studio-api/document-processing/annotations.md
        + basic_ocr.md (pinned) + context7.
"""
import json
import os
import sys
from typing import List

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.models import DocumentURLChunk
from mistralai.extra import response_format_from_pydantic_model
from pydantic import BaseModel, Field

load_dotenv()

# A stable public document to extract from (first page only, to stay cheap/fast).
DOC_URL = "https://arxiv.org/pdf/2201.04234"


class DocMeta(BaseModel):
    language: str = Field(..., description="The primary language of the document.")
    title: str = Field(..., description="The document title.")
    keywords: List[str] = Field(..., description="A few key topic words.")


def extract(client):
    """OCR the first page and return the typed annotation."""
    resp = client.ocr.process(
        model="mistral-ocr-latest",
        document=DocumentURLChunk(document_url=DOC_URL),
        document_annotation_format=response_format_from_pydantic_model(DocMeta),
        pages=[0],
    )
    return resp.document_annotation


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    annotation = extract(client)
    print(f"document_annotation={annotation!r}")

    # Acceptance contract: we got a structured annotation that parses into DocMeta.
    assert annotation, "no structured annotation returned (document_annotation_format not applied)"
    meta = DocMeta.model_validate_json(annotation)
    assert meta.language, "language field empty"
    assert meta.title, "title field empty"
    print(f"PARSED language={meta.language!r} title={meta.title!r} keywords={meta.keywords}")
    print("TASK3 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK3 FAIL: {e}")
        sys.exit(1)
