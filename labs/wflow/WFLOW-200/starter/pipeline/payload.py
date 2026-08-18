"""WFLOW-200 Task 5 (STARTER): payload basics — pass large data by reference, not by value.

This version puts the (potentially >2MB) transcript on the orchestration layer as a plain
string, and the workflow body unwraps it. Fix both per tasks.md T5: make the large field an
OffloadableField on an OffloadableModel, and stop unwrapping it in the workflow body.

Grounded in: building-workflows/payload_offloading.md (Activity field offloading).
"""
from __future__ import annotations

from mistralai.workflows.core.encoding.fields_offloader import (  # noqa: F401
    OffloadableField,
    OffloadableModel,
)
from pydantic import BaseModel

import mistralai.workflows as workflows


# TODO(T5): make TranscriptionPayload subclass OffloadableModel and make `transcript`
# an OffloadableField[str] so the large value is passed by reference, not by value.
class TranscriptionPayload(BaseModel):
    audio_id: str
    transcript: str = ""


class SummaryInput(BaseModel):
    transcript: str = ""


@workflows.activity()
async def transcribe(payload: TranscriptionPayload) -> TranscriptionPayload:
    text = f"transcript-of-{payload.audio_id}: " + ("word " * 8).strip()
    return TranscriptionPayload(audio_id=payload.audio_id, transcript=text)


@workflows.activity()
async def summarize(data: SummaryInput) -> dict:
    full = data.transcript
    return {"summary": full[:20], "chars": len(full)}


@workflows.workflow.define(name="transcribe-workflow")
class TranscribeWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, audio_id: str) -> dict:
        result = await transcribe(TranscriptionPayload(audio_id=audio_id))
        # TODO(T5): pass result.transcript through as-is; do NOT read the value in the body.
        return await summarize(SummaryInput(transcript=result.transcript.get_value()))
