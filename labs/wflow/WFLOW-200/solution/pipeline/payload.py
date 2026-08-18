"""WFLOW-200 Task 5 (SOLUTION): payload basics — pass large data by reference, not by value.

Workflows caps workflow/activity inputs and outputs at 2MB. For a value that can exceed that
(a transcript, an extracted document body), you do NOT put the bytes on the orchestration
layer. You mark the field **offloadable**: the SDK stores it in your blob storage on the way
out of an activity and rehydrates it on the way into the next, so the orchestrator only ever
sees a small reference.

Two rules make this correct:
- The large field is an `OffloadableField` on a model that subclasses `OffloadableModel`.
- You call `.get_value()` ONLY inside activities. In the workflow body the value may not be
  local, so you pass the `OffloadableField` object through untouched.

Grounded in: building-workflows/payload_offloading.md (Activity field offloading).
"""
from __future__ import annotations

from mistralai.workflows.core.encoding.fields_offloader import (
    OffloadableField,
    OffloadableModel,
)

import mistralai.workflows as workflows


class TranscriptionPayload(OffloadableModel):
    audio_id: str  # small reference — stays on the orchestration layer
    transcript: OffloadableField[str] = OffloadableField(value="")  # large — offloaded


class SummaryInput(OffloadableModel):
    transcript: OffloadableField[str] = OffloadableField(value="")


@workflows.activity()
async def transcribe(payload: TranscriptionPayload) -> TranscriptionPayload:
    # Inside an activity the value is local, so producing/reading it is fine here.
    text = f"transcript-of-{payload.audio_id}: " + ("word " * 8).strip()
    return TranscriptionPayload(
        audio_id=payload.audio_id,
        transcript=OffloadableField(value=text),
    )


@workflows.activity()
async def summarize(data: SummaryInput) -> dict:
    # The offloaded field is rehydrated for us here; get_value() is safe INSIDE an activity.
    full = data.transcript.get_value()
    return {"summary": full[:20], "chars": len(full)}


@workflows.workflow.define(name="transcribe-workflow")
class TranscribeWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, audio_id: str) -> dict:
        result = await transcribe(TranscriptionPayload(audio_id=audio_id))
        # Pass the offloaded field through as-is — do NOT unwrap it in the workflow body.
        return await summarize(SummaryInput(transcript=result.transcript))
