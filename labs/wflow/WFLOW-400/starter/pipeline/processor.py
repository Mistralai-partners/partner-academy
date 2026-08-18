"""WFLOW-400 Task 1 + Task 2 (STARTER): fix determinism, then build the four-constraint design.

This starter is DELIBERATELY BROKEN. Two jobs:

  Task 1 (determinism). The `run` entrypoint calls non-deterministic standard-library APIs
  (datetime.now, uuid.uuid4, random) and does I/O directly in the workflow body. Replace them
  with deterministic workflow APIs (workflow.now / workflow.uuid4 / workflow.random) and move
  every side effect into an @activity.

  Task 2 (the Create item). Rework this into ONE workflow that satisfies FOUR hard constraints:
    1. payloads > 2MB          -> activity-field offloading (OffloadableModel / OffloadableField)
    2. encrypted at rest       -> EncryptedStrField on the PII field
    3. indefinite runtime      -> continue-as-new with carry-forward state parameters
    4. per-iteration determinism-> all I/O in granular activities (>= 3), pure orchestration body

See ../../README.md and ../../tasks.md. Reference: ../../solution/pipeline/processor.py.
"""
from __future__ import annotations

import datetime
import random
import uuid

from pydantic import BaseModel

import mistralai.workflows as workflows


# BUG (Task 2): a plain model. Nothing is offloaded and nothing is encrypted.
class PagePayload(BaseModel):
    doc_id: str
    customer_ssn: str          # BUG: PII stored in cleartext, not EncryptedStrField
    body: str = ""             # BUG: large body not offloaded (> 2MB will exceed the limit)


class ProcessorState(BaseModel):
    doc_id: str
    page: int = 0
    total_processed: int = 0


@workflows.workflow.define(name="pii-safe-processor")
class PiiSafeProcessor:
    @workflows.workflow.entrypoint
    async def run(self, doc_id: str) -> int:              # BUG (Task 2): no carry-forward state params
        # BUG (Task 1): non-deterministic calls + direct I/O in the workflow body.
        run_id = uuid.uuid4()
        started_at = datetime.datetime.now()
        jitter = random.random()

        total_processed = 0
        page = 0
        # BUG (Task 1): file/network I/O directly in the workflow body (must live in an activity).
        with open("/etc/hostname") as fh:
            _ = fh.read()

        # BUG (Task 2): no activities, no continue-as-new -> not durable, will hit history limits.
        payload = PagePayload(doc_id=doc_id, customer_ssn="000-00-0000", body="<page text>")
        total_processed += len(payload.body)
        return total_processed
