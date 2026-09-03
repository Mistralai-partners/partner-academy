"""WFLOW-400 Task 1 + Task 2 (SOLUTION): a PII-safe, indefinitely long-running processor.

This one workflow satisfies FOUR simultaneous hard constraints (the L400 Create item):

  1. Payloads > 2MB          -> activity-field offloading (OffloadableModel / OffloadableField).
                                The orchestration layer enforces a 2MB limit on workflow and
                                activity I/O; the large body is stored in your blob storage and
                                only a reference crosses the platform.
  2. Encrypted at rest       -> EncryptedStrField on the PII column. Payloads are encrypted on
                                the worker (AES-GCM) before they leave; the platform stores
                                ciphertext only.
  3. Indefinite runtime      -> continue-as-new carries state forward and resets the event
                                history before it approaches the ~51,200-event / 50MB cap.
  4. Per-iteration determinism-> the workflow body is PURE orchestration. Every side effect and
                                every non-deterministic value lives in an activity or in a
                                deterministic workflow API (workflow.now / uuid4 / random).

Grounded in: building-workflows/payload_offloading.md, building-workflows/encryption.md,
building-workflows/continue_as_new.md, building-workflows/workflows/determinism.md,
building-workflows/activities/basics.md.
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from mistralai.workflows.core.encoding.fields_offloader import (
    OffloadableModel,
    OffloadableField,
)
# EncryptedStrField transitively imports httpx, which subclasses urllib.request.Request at
# import time; the determinism sandbox rejects that. Shield the import so the sandbox passes
# it through (documented remedy: workflow.unsafe.imports_passed_through).
with workflow.unsafe.imports_passed_through():
    from mistralai.extra.workflows.encoding import EncryptedStrField


# --- Constraint 1 + 2: large field offloaded, PII field encrypted at rest ------------
class PagePayload(OffloadableModel):
    doc_id: str
    customer_ssn: EncryptedStrField                        # Constraint 2: encrypted before it leaves the worker
    body: OffloadableField[str] = OffloadableField(value="")  # Constraint 1: offloaded when large


# --- Constraint 4: every side effect is a small, granular activity -------------------
@workflows.activity()
async def fetch_page(doc_id: str, page: int) -> PagePayload:
    """Real I/O (HTTP / DB / file) belongs in an activity, never in the workflow body."""
    return PagePayload(
        doc_id=doc_id,
        customer_ssn=EncryptedStrField(data="000-00-0000"),
        body=OffloadableField(value=f"<page {page} text of {doc_id}>"),
    )


@workflows.activity()
async def summarize_page(payload: PagePayload) -> str:
    """LLM / non-deterministic work is safe here. Unwrap the offloaded field ONLY in an activity."""
    text = payload.body.get_value()
    return f"summary:{payload.doc_id}:{len(text)}"


@workflows.activity()
async def persist_summary(doc_id: str, page: int, summary: str) -> int:
    """Idempotent write, isolated so only this step retries if the write fails."""
    return 1


class ProcessorState(BaseModel):
    doc_id: str
    page: int = 0
    total_processed: int = 0


@workflows.workflow.define(name="pii-safe-processor")
class PiiSafeProcessor:
    @workflows.workflow.entrypoint
    async def run(self, doc_id: str, page: int = 0, total_processed: int = 0) -> int:
        # Constraint 4: deterministic APIs only. Never datetime.now()/uuid.uuid4()/random/open here.
        run_id = workflow.uuid4()
        started_at = workflow.now()

        while True:
            payload = await fetch_page(doc_id, page)
            # Pass the offloaded field THROUGH to the next activity; do not unwrap in the workflow.
            summary = await summarize_page(payload)
            total_processed += await persist_summary(doc_id, page, summary)
            page += 1

            # Constraint 3: reset history while staying logically alive.
            if workflows.workflow.should_continue_as_new():
                workflows.workflow.continue_as_new(
                    ProcessorState(doc_id=doc_id, page=page, total_processed=total_processed)
                )

        return total_processed
