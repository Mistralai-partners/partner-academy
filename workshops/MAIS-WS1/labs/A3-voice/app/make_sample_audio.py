"""Mint a synthetic TWO-SPEAKER support-call sample for the A3 voice lab.

This clip is generated for the lab. It synthesizes a short dialogue between a
customer and an agent using two distinct preset voices, then concatenates the
turns into one clip so diarization can separate the speakers (speaker_1,
speaker_2). The script embeds the domain terms the acceptance check looks for:
Voxtral, AI Studio, A-1042, refund, escalation.
"""

import base64
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

# Two distinct preset voices give diarization a clear signal to separate.
CUSTOMER_VOICE = "a3e41ea8-020b-44c0-8d8b-f6cc03524e31"  # Jane (female)
AGENT_VOICE = "c69964a6-ab8b-4f8a-9465-ec0925096ec8"     # Paul, Neutral (male)

# Two turns; the domain terms are split across the two speakers.
TURNS = [
    (CUSTOMER_VOICE,
     "Hi, I'm calling about a refund on order A-1042. "
     "I was told to ask about my Voxtral subscription."),
    (AGENT_VOICE,
     "Thank you for calling AI Studio support. I can see order A-1042. "
     "I will open an escalation to the billing team so they process the refund today."),
]

OUTPUT_FILE = "sample.mp3"


def main():
    load_dotenv()
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    # Synthesize each turn with its own voice, then concatenate the mp3 bytes.
    audio_bytes = b""
    for voice_id, text in TURNS:
        response = client.audio.speech.complete(
            model="voxtral-mini-tts-2603",
            input=text,
            voice_id=voice_id,
            response_format="mp3",
        )
        audio_bytes += base64.b64decode(response.audio_data)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(audio_bytes)

    print(f"Wrote {OUTPUT_FILE} ({len(audio_bytes)} bytes) from a synthetic two-speaker lab clip.")


if __name__ == "__main__":
    main()
