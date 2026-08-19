"""Transcribe the sample support call with Voxtral and write transcript.json.

This is the reference solution. It mints sample.mp3 if it is missing, then calls
Voxtral transcription with context_bias set to the domain terms. Context bias
boosts recognition of product names and ids that are easy to mis-hear.

Run:
    uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python transcribe.py
"""

import json
import os
import subprocess
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

SAMPLE_FILE = "sample.mp3"
TRANSCRIPT_FILE = "transcript.json"

# Domain terms that matter for this support-call transcript. These are the same
# terms the acceptance check expects, and the same terms we boost with context_bias.
DOMAIN_TERMS = ["Voxtral", "AI Studio", "A-1042", "refund", "escalation"]


def ensure_sample():
    """Mint sample.mp3 if it is not present. The clip is synthetic, generated for the lab."""
    if not os.path.exists(SAMPLE_FILE):
        subprocess.run([sys.executable, "make_sample_audio.py"], check=True)


def main():
    load_dotenv()
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    ensure_sample()
    with open(SAMPLE_FILE, "rb") as f:
        content = f.read()

    response = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"file_name": SAMPLE_FILE, "content": content},
        language="en",
        # context_bias items must be whitespace/comma-free; split multi-word terms.
        context_bias=[w for t in DOMAIN_TERMS for w in t.split()],
        diarize=True,
        timestamp_granularities=["segment"],
    )

    text = response.text

    # segments is a confirmed response field: an optional list of segment chunks,
    # each with id/start/end/text. Per-segment speaker attribution is not confirmed,
    # so the speaker-turn count stays conditional. If a speaker attribute is present,
    # count distinct speakers. Otherwise leave the count at 0 and let verify skip the
    # speaker check.
    segments = getattr(response, "segments", None) or []

    speakers = set()
    for seg in segments:
        speaker = getattr(seg, "speaker", None)  # [VERIFY] per-segment speaker attribute name
        if speaker is not None:
            speakers.add(speaker)
    speaker_turns = len(speakers)

    result = {
        "text": text,
        "speaker_turns": speaker_turns,
        "segments": [
            {
                "id": getattr(s, "id", None),
                "start": getattr(s, "start", None),
                "end": getattr(s, "end", None),
                "text": getattr(s, "text", None),
            }
            for s in segments
        ],
    }

    with open(TRANSCRIPT_FILE, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(json.dumps(result, indent=2, default=str))

    # Output format by surface. Decide before you ship the transcript downstream:
    #   Live agent: request pcm audio for lowest latency.
    #   Storage or downstream summarization: keep a compressed artifact like this
    #   transcript.json alongside the mp3 sample.


if __name__ == "__main__":
    main()
