"""Objective acceptance check for the A3 voice lab.

Default mode: read transcript.json and expected.json. Assert every expected
keyword appears in the transcript text (case-insensitive). If speaker-turn data
is present, assert at least min_speaker_turns turns. Exit 0 only when the bar
is met. Exit 1 otherwise.

Selftest mode: run offline against a canned passing transcript and a canned
failing one to prove the checker logic. Exit 0.

Run:
    uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python verify.py --selftest
    uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python verify.py
"""

import argparse
import json
import sys

TRANSCRIPT_FILE = "transcript.json"
EXPECTED_FILE = "expected.json"


def check(transcript, expected):
    """Return (ok, messages).

    Messages read like an incident report. They teach why a check failed and
    point at the evidence, not at the code fix.
    """
    messages = []
    ok = True

    text = transcript.get("text") or ""
    haystack = text.lower()

    # Keyword acceptance: every expected term must appear, case-insensitive.
    for keyword in expected.get("expected_keywords", []):
        if keyword.lower() not in haystack:
            ok = False
            messages.append(
                f"Acceptance failed: expected keyword '{keyword}' not found in the "
                f"transcript. It was likely transcribed as a near-miss, for example a "
                f"product name heard as two common words ('Voxtral' as 'vox trial') or "
                f"an order id heard as loose digits. Add it to context_bias and reason "
                f"about why detection missed a known term, rather than lengthening the input."
            )

    # Speaker-turn acceptance: only enforced when diarization data is present.
    turns = transcript.get("speaker_turns", 0)
    min_turns = expected.get("min_speaker_turns", 0)
    if turns and turns > 0:
        if turns < min_turns:
            ok = False
            messages.append(
                f"Acceptance failed: found {turns} speaker turn(s) but the bar is "
                f"{min_turns}. The transcript did not separate speakers. Confirm diarize "
                f"was requested, then inspect whether the clip actually carries more than "
                f"one speaker before you change the acceptance bar."
            )
    else:
        messages.append(
            "Note: no speaker-turn data present, so the diarization check is skipped. "
            "This is expected for a single-speaker synthetic clip."
        )

    if ok:
        messages.append("Acceptance passed: all expected keywords present.")
    return ok, messages


def selftest():
    """Prove the checker logic offline. No network, no files, no API key."""
    expected = {"expected_keywords": ["Voxtral", "refund"], "min_speaker_turns": 2}

    passing = {"text": "You asked about a refund on Voxtral.", "speaker_turns": 0}
    ok, _ = check(passing, expected)
    assert ok is True, "selftest failed: canned passing transcript should pass"

    failing = {"text": "You asked about a return on vox trial.", "speaker_turns": 0}
    ok, _ = check(failing, expected)
    assert ok is False, "selftest failed: canned failing transcript should fail"

    print("Selftest passed: checker accepts a good transcript and rejects a bad one.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Acceptance check for the A3 voice lab.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the offline checker logic tests and exit.",
    )
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    with open(TRANSCRIPT_FILE) as f:
        transcript = json.load(f)
    with open(EXPECTED_FILE) as f:
        expected = json.load(f)

    ok, messages = check(transcript, expected)
    for m in messages:
        print(m)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
