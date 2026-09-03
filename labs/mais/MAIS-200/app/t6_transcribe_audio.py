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
import base64
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "voxtral-mini-latest"
TTS_MODEL = "voxtral-mini-tts-2603"

# What we synthesize, then transcribe back. Keeping the phrase here lets the run be
# fully self-contained (no committed audio fixture) and lets you eyeball that the
# transcript matches what was spoken.
SAMPLE_TEXT = "Hello from Mistral Studio, testing text to speech."


def make_sample_audio(client, text=SAMPLE_TEXT):
    """Synthesize a short mp3 with Voxtral TTS so the lab has audio to transcribe
    without shipping a binary fixture. Returns raw mp3 bytes."""
    voice = client.audio.voices.list().items[0]
    resp = client.audio.speech.complete(
        model=TTS_MODEL,
        input=text,
        voice_id=voice.id,
        response_format="mp3",
        stream=False,
    )
    return base64.b64decode(resp.audio_data)


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

    # Generate the input audio in-process (TTS), then transcribe it. No fixture file
    # to clone, and it demonstrates the TTS -> transcription round-trip end to end.
    audio = make_sample_audio(client)
    print(f"synthesized {len(audio)} bytes of sample audio via Voxtral TTS")

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
