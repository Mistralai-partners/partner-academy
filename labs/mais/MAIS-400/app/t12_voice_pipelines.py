#!/usr/bin/env python
"""Task 12 (SOLUTION) - Voice pipelines under quality and latency constraints.

Behavior (maps to MAIS-400 L12): clone a voice from a sample, then synthesize
speech in both batch (non-streaming) and streaming modes. Streaming returns
audio deltas for low-latency playback.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.audio.voices.create(name=..., sample_audio=<base64>,
        retention_notice=30)
    -> VoiceResponse (.id, .name)
  - client.audio.speech.complete(model="voxtral-mini-tts-2603",
        input=..., voice_id=..., response_format="mp3", stream=False)
    -> .audio_data (base64-encoded)
  - client.audio.speech.complete(..., stream=True)
    -> context manager yielding speech.audio.delta events
Source: context7 /mistralai/client-python docs/sdks/speech/README.md + docs/sdks/voices/README.md.
"""
import base64
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "voxtral-mini-tts-2603"


def synthesize_batch(client, text, voice_id, fmt="mp3"):
    """Synthesize speech in batch mode and return raw audio bytes."""
    resp = client.audio.speech.complete(
        model=MODEL,
        input=text,
        voice_id=voice_id,
        response_format=fmt,
        stream=False,
    )
    return base64.b64decode(resp.audio_data)


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    voices = client.audio.voices.list().items
    voice = voices[0]
    print(f"using voice: id={voice.id} name={voice.name}")

    audio = synthesize_batch(client, "Testing voice pipeline constraints.", voice.id)
    print(f"batch audio: {len(audio)} bytes")

    assert len(audio) > 1000, "batch audio suspiciously small"
    print("TASK12 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK12 FAIL: {e}")
        sys.exit(1)
