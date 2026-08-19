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

# The domain terms that matter for this support-call transcript.
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

    # TODO: set context_bias for the domain terms
    context_bias_unset = []

    response = client.audio.transcriptions.complete(
        model="voxtral-mini-latest",
        file={"file_name": SAMPLE_FILE, "content": content},
        language="en",
        context_bias=context_bias_unset,
        diarize=True,
    )

    # TODO: extract the transcript and speaker turns into transcript.json
    result = {}

    with open(TRANSCRIPT_FILE, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
