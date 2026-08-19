# A3 tasks: Voice Transcription with an Acceptance Check

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

## Behavior you build

You transcribe a support call with Voxtral and prove the transcript meets an
objective acceptance bar. The bar: every expected domain keyword is present, and
speakers are separated when the model returns speaker data. You then decide the
output format for the target surface.

## Prerequisites

- Python 3.10 or later and `uv`.
- `MISTRAL_API_KEY` in your environment or in a `.env` file. Bring your own key.
- No external audio file. You mint a synthetic sample in Task 1.

Work inside `starter/`. The `solution/` folder holds a complete reference if you
get stuck. Every command runs the file in the current folder, so `cd` into the
folder you are working in first.

## Done when

You are done when `verify.py` exits 0. See `VERIFY.md` for the full contract.

All commands use the same runner so you do not need a project setup:

```
uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python <file>
```

---

## Task 0: Prove the checker logic offline

- Objective: Run the acceptance checker in selftest mode to see how
  a good transcript passes and a bad one fails, before you touch the API.
- Scenario: On the job you trust a check only after you have seen it reject a
  known-bad input. Confirm the checker is honest first.
- Command:
  ```
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python verify.py --selftest
  ```
- Hint (evidence): Read the two canned cases in `verify.py`. Notice the failing
  case mis-spells a product name the way a model might mis-hear it.
- Acceptance: The command prints "Selftest passed" and exits 0. This works even
  before you fill in any TODO.

## Task 1: Mint the sample audio

- Objective: Generate a short, synthetic support-call clip so the lab is
  self-contained.
- Scenario: You rarely have a clean, labeled clip on hand. Here you synthesize
  known text so you know exactly what a correct transcript should contain.
- Command:
  ```
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python make_sample_audio.py
  ```
- Hint (evidence): Open `make_sample_audio.py` and read `SAMPLE_SCRIPT`. Those are
  the exact terms the checker will look for. The clip is single-speaker by design.
- Acceptance: The command writes `sample.mp3` and prints its byte size.

## Task 2: Transcribe and write the artifact

- Objective: Transcribe `sample.mp3` with Voxtral and write
  `transcript.json` with the text and any speaker turns.
- Scenario: Downstream summarization consumes a structured transcript, not a raw
  API response. You produce that artifact.
- Fill the TODOs in `starter/transcribe.py`:
  - Set `context_bias` for the domain terms.
  - Extract the transcript text and speaker turns into `transcript.json`.
- Command:
  ```
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python transcribe.py
  ```
- Hint (evidence): The response has a `.text` field and an optional `.segments`
  list. Read `expected.json` to see which terms and how many speaker turns the
  bar requires.
- Acceptance: The command writes `transcript.json` and prints it.

## Task 3: Meet the acceptance bar

- Objective: Run the checker, read any failure as a diagnosis, and act
  on the evidence until the bar is met.
- Scenario: A transcript that drops a product name or an order id is unsafe to
  hand downstream. You prove yours is safe.
- Command:
  ```
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python verify.py
  ```
- Hint (evidence): If a keyword fails, open `transcript.json` and find how the
  model actually heard that term. Ask why a short, branded term was missed.
  `VERIFY.md` walks through the diagnosis. The fix is a direction, not a snippet.
- Acceptance: `verify.py` exits 0 and prints "Acceptance passed".

## Task 4: Choose the output format by surface

- Objective: Decide which audio and transcript format fits the target
  surface, and record your reasoning.
- Scenario: The same transcript can feed a live agent or a storage pipeline. The
  right format differs.
- Hint (evidence): Read the format comments in `make_sample_audio.py` and the
  closing comment in `solution/transcribe.py`. Compare pcm for live latency
  against a compressed artifact for storage and summarization.
- Acceptance: In one or two sentences, state which format you would ship for a
  live agent and which for storage, and why. No command. This is a judgment call.

---

## Stretch: one speech-to-speech turn

- Objective: Run a single realtime speech-to-speech turn on the
  sample and confirm the spoken response meets a content acceptance check.
- Scenario: A voice agent needs to hear, reason, and speak back. This previews
  that surface.
- Note on setup: the realtime surface needs the realtime extra:
  ```
  uv run --no-project --with 'mistralai[realtime]==2.9.3' --with python-dotenv python <your_script>
  ```
- Hint (evidence): Feed the same `sample.mp3` in and capture the spoken reply.
  Transcribe the reply and reuse the same keyword check idea to confirm the agent
  addressed the refund and the escalation.
- The exact realtime speech-to-speech method is unconfirmed: `[VERIFY]` the
  realtime speech-to-speech method name in the installed SDK before you rely on it.
- Acceptance: The spoken response, once transcribed, contains the content terms
  you expect (for example refund and escalation).
