# Acceptance contract

The objective definition of done for A3, enforced by `verify.py`.

## What "done" means

Your transcript is accepted when both conditions hold:

- Every expected domain keyword appears in the transcript text, matched
   case-insensitively. The keywords live in `expected.json` under
   `expected_keywords`: Voxtral, AI Studio, A-1042, refund, escalation.
- Speakers are separated when diarization data is present. This condition is
   conditional. If the response carries per-segment speaker data, the checker
   requires at least `min_speaker_turns` distinct speakers (2). If no speaker
   data is present, the checker skips this part and says so. The synthetic
   sample is single-speaker, so expect the speaker check to be skipped unless
   you supply richer audio.

`verify.py` reads `transcript.json` and `expected.json`, applies both rules, and
exits 0 only when the bar is met. It exits 1 otherwise.

## How to read the output

- Exit 0 with "Acceptance passed: all expected keywords present." means the
  transcript meets the bar. You are done.
- Exit 1 with one or more "Acceptance failed:" lines means the bar is not met.
  Each line is written like an incident report. It names the evidence and the
  likely cause, and it points you at a direction to investigate.
- A "Note:" line about skipped diarization is informational, not a failure.

To prove the checker itself works before you run against the API, run it offline:

```
uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python verify.py --selftest
```

That runs the checker against a canned passing transcript and a canned failing
one, then exits 0.

## The common failure, framed as diagnosis

The most common failure is a domain term that gets mis-transcribed. A product
name like "Voxtral" can be heard as two ordinary words ("vox trial"), and an
order id like "A-1042" can be heard as loose digits. When that happens, the
keyword check cannot find the term and acceptance fails.

Diagnose it, do not paper over it:

- Read the failing keyword in the checker output.
- Open `transcript.json` and find how the model actually heard that term.
- Ask why the model missed a known, business-critical term. Short, unusual, or
  branded terms carry little acoustic context, so the model guesses common words.
- Bias the model toward the terms you know are coming. The transcription call
  accepts a list of terms (`context_bias`) for exactly this purpose. Adding the term
  to that list raises the odds it is recognized. Lengthening or re-recording the input
  does not address the root cause.
- Mind the `context_bias` contract: each item must be a single token with no
  whitespace and no commas. A multiword name like "AI Studio" is rejected as-is, so
  split it into "AI" and "Studio". The transcript text still reads back the full
  phrase, so the acceptance keyword "AI Studio" is unaffected.
- If you enable diarization, pass `timestamp_granularities=["segment"]` alongside
  `diarize=True`. Segment timing is what the model uses to attribute speaker turns,
  so the API rejects diarization without it.
