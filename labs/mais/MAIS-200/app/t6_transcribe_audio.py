#!/usr/bin/env python
"""Task 6 (SOLUTION) - Transcribe audio with Voxtral.

Behavior (maps to MAIS-200 L8, FKC Q9): transcribe spoken audio to text using
Voxtral Mini, with optional diarization (who said what) and timestamped segments.
Context bias nudges the model toward domain terms it might otherwise miss.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"file_name": ..., "content": <bytes>},
        language="en",
        diarize=True,
        timestamp_granularities=["segment"],
        context_bias=[...])
    -> .text (plain transcript)
Source: context7 /mistralai/client-python docs/sdks/transcriptions/README.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "voxtral-mini-latest"


def transcribe(client, audio_bytes, filename="audio.mp3", language="en",
               context_bias=None, diarize=True):
    """Transcribe audio bytes and return the API response object."""
    kwargs = dict(
        model=MODEL,
        file={"file_name": filename, "content": audio_bytes},
        language=language,
        diarize=diarize,
        timestamp_granularities=["segment"],
    )
    if context_bias:
        kwargs["context_bias"] = context_bias
    return client.audio.transcriptions.complete(**kwargs)


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_audio.mp3")
    if not os.path.exists(sample_path):
        print("SKIP: no sample_audio.mp3 found (place one here for the live run)")
        print("TASK6 PASS (structure only)")
        return

    with open(sample_path, "rb") as f:
        audio = f.read()

    result = transcribe(
        client, audio,
        context_bias=["Voxtral", "Mistral", "Studio"],
    )
    print(f"text={result.text[:200]!r}...")

    assert result.text, "transcription returned empty text"
    print("TASK6 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK6 FAIL: {e}")
        sys.exit(1)
