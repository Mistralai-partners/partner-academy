# Tasks: Build a Guarded Agent

## Behavior you build

- A fintech support agent that completes an allowed order-status task and refuses a disallowed request mixing a card number with an investment question.
- The guardrail is attached at the agent level and on the risky conversation call.

## Prerequisites

- Python 3.10 or later and `uv` installed.
- Your own `MISTRAL_API_KEY` in a `.env` file next to the scripts.
- Work in the `starter/` folder. Compare with `solution/` only after you try.

## Done when

- `verify.py` exits 0: the allowed turn is tool-backed and names the order and a status, and the disallowed turn is blocked with no card echo and no advice.

## How results flow

- `build_agent.py` runs the two turns and writes `results.json`; `verify.py` reads that artifact and grades it, which keeps grading stable and separate from live-call timing.
- Run `build_agent.py` first, then `verify.py`.

## Run commands

Run these from inside `starter/`.

```
# 1. Offline self-test. No network. Proves the tool and the moderation gate work.
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python build_agent.py --selftest

# 2. Build and run the two live turns. Writes results.json.
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python build_agent.py

# 3. Grade the run.
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python verify.py

# You can also prove the checker itself offline:
uv run --no-project --with 'mistralai>=2.7' --with python-dotenv python verify.py --selftest
```

---

## Task 1: Confirm the scaffold runs

- **Objective:** Run the offline self-test and identify that the tool and the
  moderation gate already work before you touch the live path.
- **Scenario:** On the job you confirm the harness is healthy before you blame your code.
  A green offline check tells you the base is sound.
- **Hint:** Look at the self-test output. It reports the order lookup and the moderation
  gate separately. If both pass, the gaps you need to fix are elsewhere.
- **Acceptance:** `build_agent.py --selftest` prints `selftest PASS` and exits 0.

## Task 2: Run the build and read the incident report

- **Objective:** Run the build and the checker as shipped, then analyze the two
  findings to locate where behavior breaks.
- **Scenario:** A customer files a bug. Your first move is to reproduce it and read the
  evidence, not to guess at the code.
- **Hint:** The checker prints one finding per problem. Note which turn fails and what
  the evidence says. One finding is about a missing status. Another is about a request
  that went through ungated. Read them as symptoms.
- **Acceptance:** `verify.py` exits 1 and prints findings for both turns. You can state,
  in your own words, what each finding observed.

## Task 3: Make the allowed turn tool-backed

- **Objective:** Apply the tool-result pattern so the assistant receives the
  order data and the turn reports a real status.
- **Scenario:** A tool that runs but never returns its result is worse than no tool. The
  agent answers with confidence and no data. You must carry the tool output back into
  the turn, and a lookup that misses must return an error result, never throw.
- **Hint:** The checker says the allowed turn is not tool-backed and has no status. Trace
  where the model asks for the order. Ask what happens to that request next. The evidence
  is the empty status, not a specific line to copy.
- **Acceptance:** In the next run, the allowed turn shows `tool_used: True` and a status
  such as `shipped`, and the allowed check passes.

## Task 4: Make the disallowed turn actually block

- **Objective:** Diagnose why the disallowed turn is not blocked and attach the
  guardrail so it fires.
- **Scenario:** A guardrail that exists in the file but never runs is a false sense of
  safety. In a fintech product that gap leaks a card number or ships bad advice.
- **Hint:** The checker says the guardrail is defined but never attached to the risky
  conversation call. Compare the allowed turn and the disallowed turn. One attaches the
  guardrail. One does not. The evidence is the blocked flag reading false.
- **Acceptance:** In the next run, the disallowed turn shows `blocked: True`, echoes no
  card digits, and gives no advice. The disallowed check passes.

## Task 5: Confirm done

- **Objective:** Evaluate the full run against the acceptance contract and
  confirm both checks pass together.
- **Scenario:** Done means both behaviors hold at once. A fix that blocks the bad turn
  but breaks the good turn is not done.
- **Hint:** Run the build, then the checker. Read the final `RESULT` line. Both findings
  should be OK.
- **Acceptance:** `verify.py` prints `RESULT: PASS` and exits 0.

---

## Stretch: add an orchestrator to specialist handoff

- **Objective:** Create a second agent and hand off to it, then confirm the
  guardrail still holds across the handoff.
- **Scenario:** Real support flows route a shopper to a specialist, for example a returns
  agent. The safety promise must survive the routing. A guardrail that only guards the
  first hop is not enough.
- **Steps:**
  - Create a specialist agent, for example a returns agent, with its own instructions.
  - Give the orchestrator agent a handoff to the specialist. The agents API accepts a
     `handoffs=` list on `agents.create`. `[VERIFY]` the exact `handoffs=` field name and
     the id or object shape it expects in your installed version.
  - Attach the same guardrail at both agents and on the conversation call.
  - Send the disallowed prompt through the orchestrator so it routes to the specialist.
- **Hint:** Watch the disallowed turn after the handoff. If the specialist answers
  without the guardrail, the block disappears. The evidence is the blocked flag on the
  post-handoff turn.
- **Acceptance:** The disallowed turn stays blocked after the handoff, and the allowed
  order-status turn still completes.
