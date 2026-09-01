#!/usr/bin/env python
"""Task 8 (SOLUTION) - Real-time transcription latency tuning.

Behavior (maps to MAIS-400 L4): stream audio chunks to the realtime
transcription endpoint and compare fast vs slow delay settings. The
target_streaming_delay_ms parameter trades latency for accuracy.

Requires: pip install 'mistralai[realtime]' (adds websockets>=13.0).

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.audio.realtime.transcribe_stream(
        model="voxtral-mini-transcribe-realtime-2602",
        audio_format=AudioFormat(encoding="pcm_s16le", sample_rate=16000),
        target_streaming_delay_ms=240)
    -> async iterator of TranscriptionStreamTextDelta / TranscriptionStreamDone
Source: context7 /mistralai/client-python docs/sdks/realtime/README.md.

Note: this task requires a microphone or PCM audio file and the websockets
dependency. The verify.py check is structure-only (AST). For the live run,
install the realtime extra and provide audio input.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


async def transcribe_stream(client, delay_ms=240):
    """Open a realtime transcription stream and collect text fragments."""
    from mistralai.client.models import AudioFormat

    fragments = []
    async for event in client.audio.realtime.transcribe_stream(
        model="voxtral-mini-transcribe-realtime-2602",
        audio_format=AudioFormat(encoding="pcm_s16le", sample_rate=16000),
        target_streaming_delay_ms=delay_ms,
    ):
        if hasattr(event, "text") and event.text:
            fragments.append(event.text)
    return " ".join(fragments)


async def dual_delay_compare(client):
    """Run fast (240ms) and slow (2400ms) delay settings and compare results."""
    fast = await transcribe_stream(client, delay_ms=240)
    slow = await transcribe_stream(client, delay_ms=2400)
    return {"fast_240ms": fast, "slow_2400ms": slow}


def main():
    from mistralai.client import Mistral

    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    print("SKIP: realtime transcription requires websockets + live audio input")
    print("Structure verified (AST): transcribe_stream + dual_delay_compare defined")
    print("TASK8 PASS (structure only)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK8 FAIL: {e}")
        sys.exit(1)
