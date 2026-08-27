"""Transcribe the sample support call with Voxtral and write transcript.json.

This is the reference solution. It mints sample.mp3 if it is missing, then calls
Voxtral transcription with context_bias set to the domain terms, tokenized so each
item is whitespace-free and comma-free. Context bias boosts recognition of product
names and ids that are easy to mis-hear.

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
# terms the acceptance check expects in the transcript text, including the phrase
# "AI Studio" that the caller actually speaks.
DOMAIN_TERMS = ["Voxtral", "AI Studio", "A-1042", "refund", "escalation"]

# context_bias has a stricter contract than the acceptance list. Each item must be
# a single token with no whitespace and no commas, so a multiword product name like
# "AI Studio" is rejected as-is. Split multiword terms into their component words so
# each one biases recognition on its own. The transcript text still reads back the
# full phrase "AI Studio"; only the bias list is tokenized.
CONTEXT_BIAS = ["Voxtral", "AI", "Studio", "A-1042", "refund", "escalation"]


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

    # diarize=True requires timestamp_granularities=["segment"]: segment timing is
    # what the model uses to attribute speaker turns, so the API rejects diarization
    # without it. context_bias takes the tokenized, whitespace-free list.
    response = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"file_name": SAMPLE_FILE, "content": content},
        language="en",
        context_bias=CONTEXT_BIAS,
        diarize=True,
        timestamp_granularities=["segment"],
    )

    text = response.text

    # segments is a list of TranscriptionSegmentChunk, each with start/end/text and,
    # when diarization runs, a speaker_id. Count distinct speaker_id values as turns.
    # This clip is a two-speaker dialogue (customer and agent), so diarization
    # returns two distinct speaker_id values and the verify speaker check enforces them.
    segments = getattr(response, "segments", None) or []

    speakers = set()
    for seg in segments:
        speaker = getattr(seg, "speaker_id", None)  # TranscriptionSegmentChunk.speaker_id
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
