#!/usr/bin/env python
"""Task 11 (SOLUTION) - Expert Document AI: annotation schemas and confidence gating.

Behavior (maps to MAIS-400 L7): extract structured metadata from a document
using Pydantic annotation schemas, then run a confidence-scored pass to
identify pages that need human review.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.ocr.process(
        model="mistral-ocr-latest",
        document=DocumentURLChunk(document_url=...),
        document_annotation_format=response_format_from_pydantic_model(Model),
        document_annotation_prompt=...)
    -> .pages[i].markdown, .document_annotation (parsed model)
  - client.ocr.process(..., confidence_scores_granularity="page")
    -> .pages[i].confidence_score
Source: context7 /mistralai/client-python docs/sdks/ocr/README.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.models import DocumentURLChunk
from mistralai.extra import response_format_from_pydantic_model
from pydantic import BaseModel, Field

load_dotenv()

CONFIDENCE_THRESHOLD = 0.85
TEST_URL = "https://arxiv.org/pdf/2410.07073"


class Document(BaseModel):
    language: str = Field(description="Primary language of the document")
    chapter_titles: list[str] = Field(description="All section/chapter titles")
    urls: list[str] = Field(description="All URLs found in the document")


def extract_metadata(client, document_url):
    """Extract structured metadata from a document using OCR + annotation."""
    result = client.ocr.process(
        model="mistral-ocr-latest",
        document=DocumentURLChunk(document_url=document_url),
        document_annotation_format=response_format_from_pydantic_model(Document),
        document_annotation_prompt="Extract the language, all section titles, and all URLs.",
    )
    return result


def pages_needing_review(client, document_url, threshold=CONFIDENCE_THRESHOLD):
    """Return page indices with confidence below threshold."""
    result = client.ocr.process(
        model="mistral-ocr-latest",
        document=DocumentURLChunk(document_url=document_url),
        confidence_scores_granularity="page",
    )
    flagged = []
    for i, page in enumerate(result.pages):
        score = getattr(page, "confidence_score", None)
        if score is not None and score < threshold:
            flagged.append({"page": i, "score": score})
    return flagged


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    result = extract_metadata(client, TEST_URL)
    raw_annotation = result.document_annotation
    assert raw_annotation, "no document annotation returned"
    assert result.pages, "OCR returned no pages"

    annotation = Document.model_validate_json(raw_annotation)
    print(f"language={annotation.language}")
    print(f"chapters={len(annotation.chapter_titles)}")
    print(f"urls={len(annotation.urls)}")

    assert annotation.language, "annotation missing language"
    print("TASK11 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK11 FAIL: {e}")
        sys.exit(1)
