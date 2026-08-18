# A3: Voice Transcription with an Acceptance Check

## Scenario

You work at a customer support ISV. The team wants meeting and call audio turned
into a reliable transcript that downstream tools can summarize. A transcript is
useful only when it captures the terms that matter: product names, order ids, and
the words that drive action like refund and escalation. In this lab you transcribe
a support call with Voxtral, prove the transcript meets an acceptance bar, and then
decide the output format for the target surface.

## What this builds

You build a small, testable transcription step:

- Transcribe audio with Voxtral, biased toward your domain terms.
- Prove the transcript is good enough with an objective checker.
- Reason about a real failure: a domain term that gets mis-heard.
- Choose an output format by surface (live versus storage).

## Prerequisites

- Python 3.10 or later and `uv`.
- A Mistral API key in your environment as `MISTRAL_API_KEY` (bring your own).
- No external audio file. You mint a short synthetic sample in the lab.

Setup takes under 5 minutes. Put your key in a `.env` file or export it:

```
MISTRAL_API_KEY=your_key_here
```

## Done when checks pass

You are done when `verify.py` exits 0. That means every expected domain keyword
appears in the transcript, and, when the model returns speaker data, the speakers
are separated. Read the exact contract in `VERIFY.md` and the step-by-step path in
`TASKS.md`.

## What you learned and where to go next

You learned to treat a transcript as a testable artifact, to bias recognition
toward the terms your business depends on, and to pick an audio format by surface.
This maps to the Mistral AI Studio track: MAIS-200 (practitioner) leads into
MAIS-300, where you compose transcription with summarization and realtime voice
into a full support workflow.
