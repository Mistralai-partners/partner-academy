#!/usr/bin/env python
"""Task 7 (SOLUTION) - Text-to-speech with Voxtral TTS.

Behavior (maps to MAIS-200 L9): convert text to spoken audio using Voxtral Mini
TTS. The flow is: list available voices -> pick one -> synthesize speech -> decode
the base64 audio -> write to disk.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.audio.voices.list()
        -> VoiceListResponse with .items (list of VoiceResponse, each has .id, .name)
  - client.audio.speech.complete(
        model="voxtral-mini-tts-2603",
        input=<text>,
        voice_id=<id>,
        response_format="mp3",
        stream=False)
        -> .audio_data (base64-encoded string)
Source: context7 /mistralai/client-python docs/sdks/speech/README.md + docs/sdks/voices/README.md.
"""
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "voxtral-mini-tts-2603"


def list_voices(client):
    """Return a list of available VoiceResponse objects."""
    return client.audio.voices.list().items


def synthesize(client, text, voice_id, fmt="mp3"):
    """Synthesize text to audio and return raw bytes."""
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

    voices = list_voices(client)
    assert voices, "no voices available from the API"
    voice = voices[0]
    print(f"voice: id={voice.id} name={voice.name}")

    audio = synthesize(client, "Hello from Mistral Studio.", voice.id)
    out = Path(__file__).parent / "output.mp3"
    out.write_bytes(audio)
    print(f"wrote {len(audio)} bytes to {out}")

    assert len(audio) > 1000, "audio output suspiciously small"
    print("TASK7 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK7 FAIL: {e}")
        sys.exit(1)
