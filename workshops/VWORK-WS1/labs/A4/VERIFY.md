# A4: Automate and govern · VERIFY

Self-checkable acceptance. No instructor required. This is a **two-part** check; both parts must pass.

## Pass condition

**Part (a): automation runs.**
- The scheduled task or Studio workflow exists.
- It executes a run (or a first / dry run) on its schedule or trigger.
- Only read-only steps are pre-authorized; no send is pre-authorized.

**Part (b): the posture blocks a disallowed send.**
- You asked for a send to a safe test destination.
- The approval prompt appeared showing the tool call and arguments (Allow once / Always allow for this chat / Reject).
- You clicked **Reject**.
- The response reports the rejected permission ("The user rejected permission to use this specific tool call. Do not retry it.") and **no action ran** (nothing sent, nothing created).

## How to check

- Confirm the automation is listed and shows a run in its run-status indicator.
- Confirm you can see the send was held and then blocked, with no message delivered to the test destination.
- Compare against `solution/reference-automation.md` and `solution/expected-rejection.md`.

## Why this is the right check

- The evidence is that you can operate an automation and its governance, not just create a schedule.
- Part (a) proves the unattended refresh works; part (b) proves the human-in-the-loop guardrail actually blocks, with nothing sent.
- Approval is the design, not a limitation: you automate real work without giving up control of what leaves your hands.
