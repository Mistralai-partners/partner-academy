"""Transcribe the sample support call with Voxtral and write transcript.json.

Starter skeleton. Fill the TODOs to make verify.py exit 0. The skeleton imports
cleanly, and verify.py --selftest passes offline before you fill anything in.

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

# The domain terms that matter for this support-call transcript. These are what the
# acceptance check looks for in the transcript TEXT, so keep the full phrase
# "AI Studio" here.
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

    # TODO: set context_bias for the domain terms.
    # Contract: each context_bias item must be a single token with no whitespace and
    # no commas. A multiword name like "AI Studio" is rejected as-is, so split it into
    # "AI" and "Studio". The transcript text still reads back "AI Studio"; only this
    # bias list is tokenized. Aim for something like:
    #   ["Voxtral", "AI", "Studio", "A-1042", "refund", "escalation"]
    context_bias_unset = []

    # diarize=True requires timestamp_granularities=["segment"]: segment timing is what
    # the model uses to attribute speaker turns, so the API rejects diarization without
    # it. This is API contract, not part of the exercise, so it is already wired in.
    response = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"file_name": SAMPLE_FILE, "content": content},
        language="en",
        context_bias=context_bias_unset,
        diarize=True,
        timestamp_granularities=["segment"],
    )

    # TODO: extract the transcript and speaker turns into transcript.json
    result = {}

    with open(TRANSCRIPT_FILE, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
