"""Mint a synthetic support-call audio sample for the A3 voice lab.

This clip is generated for the lab. It does not use any external audio file.
You synthesize known text from a built-in preset voice with Voxtral TTS.

The synthesized script contains the domain terms the acceptance check looks for:
Voxtral, AI Studio, A-1042, refund, escalation.

Limitation: this mints a single-speaker clip from one preset voice. Minting a
reliable multi-speaker clip from one preset is not guaranteed. For that reason
the diarize acceptance check stays conditional. See verify.py and expected.json.
"""

import base64
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

# Known text to synthesize. Keep it plain: no markdown, no emojis, no special chars.
# The domain terms below are what verify.py checks for in the transcript. Some of
# them are easy to mis-hear (a product name, an order id), which is the point.
SAMPLE_SCRIPT = (
    "Hello, thank you for calling AI Studio support. "
    "I can see your order A-1042 in the system. "
    "You are asking about a refund on your Voxtral subscription. "
    "I will open an escalation to the billing team so they process the refund today."
)

# A known working preset voice id from the grounded family lab11 (Paul, Neutral).
VOICE_ID = "c69964a6-ab8b-4f8a-9465-ec0925096ec8"

# Format guidance by surface:
# pcm -> lowest streaming latency (about 0.7s time-to-first-audio). Use live.
# mp3 -> compressed. Good for storage and downloads. We use mp3 here.
# wav -> uncompressed. Highest quality.
OUTPUT_FILE = "sample.mp3"


def main():
    load_dotenv()
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    response = client.audio.speech.complete(
        model="voxtral-mini-tts-2603",
        input=SAMPLE_SCRIPT,
        voice_id=VOICE_ID,
        response_format="mp3",
    )

    # The TTS response carries base64 audio in .audio_data. Decode and write bytes.
    audio_bytes = base64.b64decode(response.audio_data)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(audio_bytes)

    print(f"Wrote {OUTPUT_FILE} ({len(audio_bytes)} bytes) from a synthetic lab clip.")


if __name__ == "__main__":
    main()
